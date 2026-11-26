"""Monte Carlo simulation of mining days with two quantum miners playing a Nash equilibrium.

Time runs on an integer clock counted in Grover iterations; one iteration takes 600/kappa seconds.
"""
import functools
import itertools
import math
import os
from dataclasses import dataclass
from multiprocessing import Pool

import numpy as np
import pandas as pd
from scipy.stats import binom as _binom

import buildpayoff as bp

CLASSICAL_STALE_RATE = 0.0024
BLOCK_SECONDS = 600.0
DAY_SECONDS = 86400.0


def _proportion_ci(p: float, n: int, z: float = 1.96) -> tuple:
    # Wilson interval — well-behaved when p is near 0 or 1
    z2 = z * z
    centre = (p + z2 / (2 * n)) / (1 + z2 / n)
    half = (z / (1 + z2 / n)) * math.sqrt(p * (1 - p) / n + z2 / (4 * n * n))
    return max(0.0, centre - half), min(1.0, centre + half)


@dataclass
class RaceOutcome:
    end_tick: int | None      # tick at which the height was settled; None if no block was ever found
    finders: list[str]        # one entry per valid block: 'Alice', 'Bob' or 'Classical'
    stale: int
    classical_ended: bool


def simulate_race(alice, bob, start_tick: int, classical_tick: int | None, p, rng,
                  baseline_stale: float = CLASSICAL_STALE_RATE) -> RaceOutcome:
    """One race for a block height, starting at start_tick.

    At each tick every scheduled measurement due is made. If any block was found (quantum success or
    classical arrival), every miner who did not measure at that tick and is not exhausted makes an
    AQMS response with the iterations accumulated since their last measurement. All valid blocks are
    found and all but one are stale; a classical block is also stale with probability baseline_stale.
    classical_tick=None disables the classical network.
    """
    strategies = {'Alice': alice, 'Bob': bob}
    schedule = {name: [start_tick + int(t) for t in itertools.accumulate(s)] for name, s in strategies.items()}
    used = {name: 0 for name in strategies}
    last = {name: start_tick for name in strategies}

    ticks = sorted({t for ts in schedule.values() for t in ts})
    if classical_tick is not None:
        ticks = sorted({t for t in ticks if t <= classical_tick} | {classical_tick})

    for tick in ticks:
        finders = []
        measured = set()
        for name, strat in strategies.items():
            while used[name] < len(strat) and schedule[name][used[name]] == tick:
                if rng.random() < p(int(strat[used[name]])):
                    finders.append(name)
                used[name] += 1
                last[name] = tick
                measured.add(name)
        classical = tick == classical_tick
        if not finders and not classical:
            continue
        for name, strat in strategies.items():
            if name not in measured and used[name] < len(strat):
                if rng.random() < p(tick - last[name]):
                    finders.append(name)
        stale = len(finders) + classical - 1
        if classical:
            finders.append('Classical')
            if rng.random() < baseline_stale:
                stale += 1
        return RaceOutcome(tick, finders, stale, classical)
    return RaceOutcome(None, [], 0, False)


@dataclass
class DayResult:
    blocks: int
    stale: int
    races: int
    classical_ended: int


class _Mixed:
    """Draws pure strategies from a mixed strategy {strategy: probability}."""

    def __init__(self, mixed: dict):
        self.strategies = list(mixed.keys())
        weights = np.array(list(mixed.values()), dtype=np.float64)
        self.cumulative = np.cumsum(weights / weights.sum())

    def draw(self, rng):
        i = int(np.searchsorted(self.cumulative, rng.random(), side='right'))
        return self.strategies[min(i, len(self.strategies) - 1)]


def simulate_day(alice_mixed: dict, bob_mixed: dict, kap: int, p, rng,
                 baseline_stale: float = CLASSICAL_STALE_RATE) -> DayResult:
    """One simulated day. Each race draws fresh pure strategies and a fresh classical arrival
    t ~ Exponential(600 s), mapped to tick start + ceil(t * kappa / 600). Races settled after the
    end of the day are not counted."""
    alice, bob = _Mixed(alice_mixed), _Mixed(bob_mixed)
    day_ticks = round(DAY_SECONDS / BLOCK_SECONDS * kap)
    tick = blocks = stale = races = classical_ended = 0
    while True:
        a, b = alice.draw(rng), bob.draw(rng)
        t = rng.exponential(BLOCK_SECONDS)
        classical_tick = tick + math.ceil(t * kap / BLOCK_SECONDS)
        out = simulate_race(a, b, tick, classical_tick, p, rng, baseline_stale)
        if out.end_tick > day_ticks:
            break
        blocks += len(out.finders)
        stale += out.stale
        races += 1
        classical_ended += out.classical_ended
        tick = out.end_tick
    return DayResult(blocks, stale, races, classical_ended)


def day_rng(seed: int, day: int) -> np.random.Generator:
    """Independent random stream for simulated day `day` under master seed `seed`."""
    return np.random.default_rng(np.random.SeedSequence(seed, spawn_key=(day,)))


_worker = None


def _init_worker(args):
    global _worker
    alice_mixed, bob_mixed, regime, W = args
    kap = bp.kappa(regime, W)
    p = _cached(bp.success_prob(regime, W))
    _worker = (alice_mixed, bob_mixed, kap, p)


def _cached(p):
    # Bounded: AQMS response counts are nearly all distinct (especially in full-header), so an
    # unbounded cache grows by millions of entries per worker over a run.
    @functools.lru_cache(maxsize=4096)
    def cached_p(k):
        return float(p(k))
    return cached_p


def _run_day(job):
    seed, day = job
    alice_mixed, bob_mixed, kap, p = _worker
    r = simulate_day(alice_mixed, bob_mixed, kap, p, day_rng(seed, day))
    return day, r.blocks, r.stale, r.races, r.classical_ended


def simulate_days(alice_mixed: dict, bob_mixed: dict, regime: str, W: float, num_days: int, seed: int,
                  processes: int | None = None, csv_path: str | None = None) -> dict:
    """Simulate num_days days in parallel and summarise the daily stale rates."""
    processes = processes or os.cpu_count() or 1
    blocks = np.zeros(num_days, dtype=np.int64)
    stale = np.zeros(num_days, dtype=np.int64)
    races = np.zeros(num_days, dtype=np.int64)
    classical_ended = np.zeros(num_days, dtype=np.int64)
    print_interval = max(1, num_days // 10)
    jobs = ((seed, day) for day in range(num_days))
    with Pool(processes, initializer=_init_worker, initargs=((alice_mixed, bob_mixed, regime, W),)) as pool:
        for i, (day, *r) in enumerate(pool.imap_unordered(_run_day, jobs, chunksize=256), 1):
            blocks[day], stale[day], races[day], classical_ended[day] = r
            if i % print_interval == 0:
                print(f"  {i}/{num_days} days simulated ({100 * i // num_days}%)", flush=True)
    return summarise(blocks, stale, races, classical_ended, csv_path)


def summarise(blocks, stale, races, classical_ended, csv_path=None) -> dict:
    """Stale-rate statistics over simulated days (and the raw per-day CSV if csv_path is given)."""
    stale_rates = np.where(blocks > 0, stale / np.maximum(blocks, 1), 0.0)
    # Per-day binomial p-value: P(X >= stale | X ~ Binom(blocks, classical rate))
    p_values = _binom.sf(stale - 1, blocks, CLASSICAL_STALE_RATE)
    n = len(stale_rates)
    prob_over_third = float(np.mean(stale_rates > 1 / 3))
    detection_prob = float(np.mean(p_values < 0.05))

    if csv_path:
        os.makedirs(os.path.dirname(csv_path) or '.', exist_ok=True)
        pd.DataFrame({
            'stale_rate': stale_rates,
            'total_blocks': blocks,
            'total_stale': stale,
            'races': races,
            'classical_ended_races': classical_ended,
            'p_value': p_values,
        }).to_csv(csv_path, index=False)
        print(f"  Raw data saved to: {csv_path}")

    return {
        'num_days': n,
        'mean_stale_rate': float(np.mean(stale_rates)),
        'std_stale_rate': float(np.std(stale_rates)),
        'p95_stale_rate': float(np.percentile(stale_rates, 95)),
        'p99_stale_rate': float(np.percentile(stale_rates, 99)),
        'max_stale_rate': float(np.max(stale_rates)),
        'prob_stale_over_third': prob_over_third,
        'prob_stale_over_third_ci': _proportion_ci(prob_over_third, n),
        'detection_prob_05': detection_prob,
        'detection_prob_05_ci': _proportion_ci(detection_prob, n),
        'avg_blocks': float(np.mean(blocks)),
        'avg_stale': float(np.mean(stale)),
        'classical_ended_share': float(classical_ended.sum() / max(races.sum(), 1)),
    }
