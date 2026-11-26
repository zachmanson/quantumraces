#!/usr/bin/env python3
"""
Expected stale blocks per race, by cause, in closed form from an equilibrium mix and p(k).

A fork leaves one stale block per valid block beyond the first, so a three-block fork counts twice.

The race is the one simulate_mining.simulate_race plays: an integer clock in Grover iterations, the
classical network arriving at tick ceil(E * kappa) with E ~ Exponential(1), and every scheduled
measurement, AQMS response and classical-triggered response counted the same way. The expectations
here are exact for that race; no simulation is run.

Causes of stale blocks in a race:
  aqms       an AQMS response succeeds after a quantum find (no tie, no classical block at that tick)
  tie        more than one scheduled measurement succeeds at the same tick
  classical  a quantum block (scheduled or response) at the tick the classical block arrives
  baseline   the classical block's own fork, probability simulate_mining.CLASSICAL_STALE_RATE

stale_per_day is races per day (day length / expected race length) times stale blocks per race; it
ignores the race cut off at the end of the day, which the simulation drops.

Run on a results folder, it reads every meta_c*_*.json below it (headline, sweep, extra equilibria),
writes one row per equilibrium, with the simulated stats beside the closed form, to
RESULTS_DIR/sweep/forks_per_race.csv, and plots the sweep rows against gamma_S to
RESULTS_DIR/sweep/images/forks_per_race_vs_gamma.pdf.

Example:
  python forks_per_race.py results_v2_g06
"""
import argparse
import itertools
import json
import math
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import buildpayoff as bp
from simulate_mining import BLOCK_SECONDS, CLASSICAL_STALE_RATE, DAY_SECONDS

matplotlib.rc('text', usetex=True)
matplotlib.rc('font', family='serif')


CAUSES = ("aqms", "tie", "classical", "baseline")


class _Clock:
    """Probabilities of the classical tick T = ceil(E * kappa), E ~ Exponential(1), and sums of p over it."""

    def __init__(self, kap: int, terms):
        self.lam = 1.0 / kap
        self.weights, angles = terms
        self.phi = 2 * np.asarray(angles)                       # sin^2(x) = (1 - cos(2x)) / 2
        self.log_z = -self.lam + 2j * self.phi                  # ratio of the geometric series in t

    def p(self, k) -> float:
        return float(np.sum(self.weights * np.sin((2 * k + 1) * self.phi / 2) ** 2))

    def p_at_least(self, t: int) -> float:
        """P(T >= t)."""
        return 1.0 if t <= 0 else math.exp(-self.lam * (t - 1))

    def p_after(self, t: int) -> float:
        """P(T > t)."""
        return math.exp(-self.lam * max(t, 0))

    def p_at(self, t: int) -> float:
        """P(T = t)."""
        return self.p_at_least(t) - self.p_after(t)

    def between(self, lo: int, hi: float) -> float:
        """P(lo <= T <= hi); hi may be math.inf."""
        return 0.0 if hi < lo else self.p_at_least(lo) - (0.0 if hi == math.inf else self.p_after(int(hi)))

    def sum_p(self, last: int, lo: int, hi: float) -> float:
        """sum_{t=lo}^{hi} P(T = t) p(t - last), lo >= 1, hi may be math.inf."""
        if hi < lo:
            return 0.0
        # P(T = t) = (1 - rho) rho^(t-1) and cos((2(t - last) + 1) phi) = Re e^{i phi (1 - 2 last)} e^{2 i phi t}
        tail = 0.0 if hi == math.inf else np.exp((hi - lo + 1) * self.log_z)
        geo = np.exp((lo - 1) * self.log_z + 2j * self.phi) * (1 - tail) / -np.expm1(self.log_z)
        cos_sum = -math.expm1(-self.lam) * np.real(np.exp(1j * self.phi * (1 - 2 * last)) * geo)
        return float(np.sum(self.weights * (self.between(lo, hi) - cos_sum)) / 2)

    def sum_survival(self, lo: int, hi: float) -> float:
        """sum_{t=lo}^{hi} P(T > t)."""
        if hi < lo:
            return 0.0
        n = math.inf if hi == math.inf else hi - lo + 1
        return self.p_after(lo) * (1.0 if n == math.inf else -math.expm1(-self.lam * n)) / -math.expm1(-self.lam)


def race_forks(alice, bob, kap: int, terms) -> dict:
    """Expected stale blocks per race by cause for the pure profile (alice, bob), plus

    aqms_responses            expected AQMS responses made after a quantum find
    aqms_response_iterations  expected total iterations those responses used
    classical_responses       expected responses made at a classical block
    length                    expected race length in ticks
    """
    clock = _Clock(kap, terms)
    schedules = [list(zip(itertools.accumulate(s), s)) for s in (alice, bob)]
    events = sorted({t for s in schedules for t, _ in s})
    out = dict.fromkeys([f"stale_{cause}" for cause in CAUSES] + ["aqms_responses", "aqms_response_iterations",
                                                                   "classical_responses", "length"], 0.0)

    def last_before(s, t):
        return max([0] + [u for u, _ in s if u < t])

    q = 1.0          # P(no scheduled measurement has succeeded before the current tick)
    prev = 0
    for t in events + [math.inf]:
        # Classical block strictly between the previous event and t: every miner with measurements left responds.
        lo = prev + 1
        hi = t - 1
        waiting = [s for s in schedules if s and s[-1][0] >= t]
        p_classical = clock.between(lo, hi)
        out["stale_classical"] += q * sum(clock.sum_p(last_before(s, t), lo, hi) for s in waiting)
        out["classical_responses"] += q * len(waiting) * p_classical
        out["stale_baseline"] += q * CLASSICAL_STALE_RATE * p_classical
        if t == math.inf:
            out["length"] += q * clock.sum_survival(prev, math.inf)
            break
        out["length"] += q * clock.sum_survival(prev, t - 1)

        due = [clock.p(k) for s in schedules for u, k in s if u == t]
        responders = [s for s in schedules if s and s[-1][0] > t and all(u != t for u, _ in s)]
        resp_p = [clock.p(t - last_before(s, t)) for s in responders]
        none_due = math.prod(1 - p for p in due)
        any_due, mean_due = 1 - none_due, sum(due)

        found = q * clock.p_after(t)                    # no classical block at t
        out["stale_tie"] += found * max(mean_due - any_due, 0.0)      # E[successes] - P(any); rounding can go below 0
        out["stale_aqms"] += found * any_due * sum(resp_p)
        out["aqms_responses"] += found * any_due * len(responders)
        out["aqms_response_iterations"] += found * any_due * sum(t - last_before(s, t) for s in responders)

        classical = q * clock.p_at(t)                # classical block at the same tick
        out["stale_classical"] += classical * (mean_due + sum(resp_p))
        out["classical_responses"] += classical * len(responders)
        out["stale_baseline"] += classical * CLASSICAL_STALE_RATE

        q *= none_due
        prev = t
    return out


def equilibrium_forks(alice_mixed: dict, bob_mixed: dict, kap: int, terms) -> dict:
    """race_forks averaged over the mixed strategies {strategy: probability}, plus

    stale_per_race          all causes together
    p_aqms_success          P(an AQMS response succeeds | one is made)
    aqms_response_fraction  E[iterations of an AQMS response | one is made] / kappa
    races_per_day           day length / expected race length
    stale_per_day           races_per_day * stale_per_race
    """
    out: dict = {}
    for (a, pa), (b, pb) in itertools.product(alice_mixed.items(), bob_mixed.items()):
        for key, value in race_forks(a, b, kap, terms).items():
            out[key] = out.get(key, 0.0) + pa * pb * value
    out["stale_per_race"] = sum(out[f"stale_{cause}"] for cause in CAUSES)
    responses = out["aqms_responses"]
    out["p_aqms_success"] = out["stale_aqms"] / responses if responses else math.nan
    out["aqms_response_fraction"] = out["aqms_response_iterations"] / responses / kap if responses else math.nan
    out["races_per_day"] = DAY_SECONDS / BLOCK_SECONDS * kap / out["length"]
    out["stale_per_day"] = out["races_per_day"] * out["stale_per_race"]
    return out


SIMULATED = ('avg_stale', 'avg_blocks', 'p95_stale_rate', 'p99_stale_rate', 'prob_stale_over_third')


def _mixed(support) -> dict:
    return {tuple(s['strategy']): s['probability'] for s in support}


def collect(results_dir: Path) -> pd.DataFrame:
    rows = []
    for path in sorted(results_dir.rglob('meta_c*_*.json')):
        meta = json.loads(path.read_text())
        terms = bp.success_terms(meta['regime'], meta['W'])
        for eq in meta.get('equilibria') or []:
            row = {'source': path.parent.relative_to(results_dir).as_posix(), 'regime': meta['regime'],
                   'c': meta['c'], 'gamma': meta['gamma'], 'n_q': meta['n_q'], 'label': eq.get('label', ''),
                   'alice_first_measurement': eq['alice_first_measurement']}
            row.update(equilibrium_forks(_mixed(eq['alice_support']), _mixed(eq['bob_support']),
                                         meta['kappa'], terms))
            row.update({key: (eq.get('stats') or {}).get(key, math.nan) for key in SIMULATED})
            rows.append(row)
    if not rows:
        return pd.DataFrame(columns=['source', 'c', 'gamma'])
    return pd.DataFrame(rows).sort_values(['regime', 'c', 'gamma', 'source'], ignore_index=True)


def plot(df: pd.DataFrame, path: Path) -> None:
    sweep = df[df['source'].str.startswith('sweep/')]
    fig, axes = plt.subplots(1, 3, figsize=(13.5, 3.2))
    for (c, group), color in zip(sweep.groupby('c'), plt.rcParams['axes.prop_cycle'].by_key()['color']):
        g = group['gamma']
        axes[0].plot(g, group['stale_per_race'], marker='o', markersize=3, color=color, label=f'$c={c}$')
        axes[0].plot(g, group['stale_aqms'], linestyle='--', color=color)
        axes[1].plot(g, group['p_aqms_success'], marker='o', markersize=3, color=color, label=f'$c={c}$')
        axes[2].plot(g, group['stale_per_day'], color=color, label=f'$c={c}$')
        axes[2].plot(g, group['avg_stale'], linestyle='none', marker='x', color=color)
    axes[0].set_ylabel(r'stale blocks per race (dashed: AQMS)')
    axes[1].set_ylabel(r'$P(\textrm{AQMS response succeeds} \mid \textrm{made})$')
    axes[2].set_ylabel(r'stale blocks per day (x: simulated)')
    for ax in axes:
        ax.set_xlabel(r'$\gamma_S$')
        ax.legend()
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path)
    plt.close(fig)
    print(f"  Plot saved to {path}")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('results_dir', type=Path)
    args = parser.parse_args()
    df = collect(args.results_dir)
    csv_path = args.results_dir / 'sweep' / 'forks_per_race.csv'
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(csv_path, index=False)
    print(f"  {len(df)} rows saved to {csv_path}")
    if len(df):
        plot(df, args.results_dir / 'sweep' / 'images' / 'forks_per_race_vs_gamma.pdf')


if __name__ == '__main__':
    main()
