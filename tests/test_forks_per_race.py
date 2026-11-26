import itertools
import math

import numpy as np
import pytest

import buildpayoff as bp
import forks_per_race as fr
import reference_model as ref
import simulate_mining as sm
from test_payoff import TOY_W, p_toy_scalar

TOY_KAPPA = bp.kappa("full-header", TOY_W)          # 43
TOY_TERMS = bp.success_terms("full-header", TOY_W)
W_2025 = ref.W_2025
KAPPA_FH = bp.kappa("full-header", W_2025)

QUANTITIES = tuple(f"stale_{cause}" for cause in fr.CAUSES) + (
    "aqms_responses", "aqms_response_iterations", "classical_responses", "length")


def classify(a, b, out):
    """Per-cause counts for one simulated race, read off the outcome and the two schedules."""
    schedules = {'Alice': list(itertools.accumulate(a)), 'Bob': list(itertools.accumulate(b))}
    t = out.end_tick
    measured = {name for name, s in schedules.items() if t in s}
    # miners who did not measure at t and still had measurements left: the ones who respond
    responders = [name for name, s in schedules.items() if name not in measured and s and s[-1] > t]
    last = {name: max([0] + [x for x in s if x < t]) for name, s in schedules.items()}
    row = dict.fromkeys(QUANTITIES, 0.0)
    row["length"] = t
    quantum = [f for f in out.finders if f != 'Classical']
    if out.classical_ended:
        row["stale_classical"] = len(quantum)
        row["stale_baseline"] = out.stale - len(quantum)
        row["classical_responses"] = len(responders)
    else:
        resp_found = sum(1 for f in quantum if f in responders)
        row["stale_aqms"] = resp_found
        row["stale_tie"] = len(quantum) - resp_found - 1
        row["aqms_responses"] = len(responders)
        row["aqms_response_iterations"] = sum(t - last[name] for name in responders)
    return row


def classical_tick(rng, kap):
    """The classical arrival tick simulate_day draws for a race starting at tick 0."""
    return math.ceil(rng.exponential(sm.BLOCK_SECONDS) * kap / sm.BLOCK_SECONDS)


def simulated_means(a, b, kap, p, n, seed):
    rng = np.random.default_rng(seed)
    rows = []
    for _ in range(n):
        out = sm.simulate_race(a, b, 0, classical_tick(rng, kap), p, rng)
        rows.append([classify(a, b, out)[q] for q in QUANTITIES])
    rows = np.array(rows, dtype=np.float64)
    return rows.mean(axis=0), rows.std(axis=0) / math.sqrt(n)


TOY_PROFILES = [
    ((10, 20), (15, 15)),          # tie at 30
    ((0, 25), (10, 5)),            # zero-iteration first measurement
    ((30,), (5,)),                 # Bob exhausted after tick 5
    ((5, 5, 20), (20, 0, 10)),     # Bob measures twice at tick 20; tie at 30
    ((43,), (43,)),                # full budget, tie at kappa
    ((20,), (40,)),
]


def assert_matches(model, sim_mean, sim_se, label):
    for q, m, s, se in zip(QUANTITIES, [model[q] for q in QUANTITIES], sim_mean, sim_se):
        z = (s - m) / max(se, 1e-9 * max(abs(m), 1))
        print(f"{label} {q}: sim={s:.6g} model={m:.6g} z={z:+.2f}")
        assert abs(z) < 4.5, f"{label} {q}: simulated {s} vs closed form {m} (z = {z:.2f})"


@pytest.mark.slow
@pytest.mark.parametrize("a,b", TOY_PROFILES)
def test_race_forks_match_simulated_races_on_the_toy_clock(a, b):
    model = fr.race_forks(a, b, TOY_KAPPA, TOY_TERMS)
    mean, se = simulated_means(a, b, TOY_KAPPA, p_toy_scalar, 200_000, seed=hash((a, b)) % 2**32)
    assert_matches(model, mean, se, f"{a} vs {b}")


FH_FRACTIONS = [((0.64,), (0.4,)), ((0.3, 0.5), (0.5, 0.3)), ((0.2, 0.2, 0.4), (0.5, 0.0, 0.25))]


@pytest.mark.slow
@pytest.mark.parametrize("fa,fb", FH_FRACTIONS)
def test_race_forks_match_simulated_races_at_full_header_scale(fa, fb):
    a = tuple(math.floor(f * KAPPA_FH) for f in fa)
    b = tuple(math.floor(f * KAPPA_FH) for f in fb)
    p = bp.success_prob("full-header", W_2025)
    model = fr.race_forks(a, b, KAPPA_FH, bp.success_terms("full-header", W_2025))
    mean, se = simulated_means(a, b, KAPPA_FH, lambda k: float(p(k)), 200_000, seed=7)
    assert_matches(model, mean, se, f"{fa} vs {fb}")


TOY_MIX_A = {(10, 20): 0.3, (30, 0): 0.5, (0, 43): 0.2}
TOY_MIX_B = {(15, 15): 0.6, (20, 5): 0.4}


@pytest.mark.slow
def test_equilibrium_ratios_match_races_drawn_from_the_mix():
    rng = np.random.default_rng(21)
    alice, bob = sm._Mixed(TOY_MIX_A), sm._Mixed(TOY_MIX_B)
    n = 200_000
    succ = resp = iters = 0.0
    for _ in range(n):
        a, b = alice.draw(rng), bob.draw(rng)
        row = classify(a, b, sm.simulate_race(a, b, 0, classical_tick(rng, TOY_KAPPA), p_toy_scalar, rng))
        succ += row["stale_aqms"]
        resp += row["aqms_responses"]
        iters += row["aqms_response_iterations"]
    model = fr.equilibrium_forks(TOY_MIX_A, TOY_MIX_B, TOY_KAPPA, TOY_TERMS)
    share = succ / resp
    assert abs(model["p_aqms_success"] - share) < 4 * math.sqrt(share * (1 - share) / resp)
    assert model["aqms_response_fraction"] == pytest.approx(iters / resp / TOY_KAPPA, rel=0.02)


@pytest.mark.slow
def test_predicted_stale_per_day_matches_simulated_days():
    days = [sm.simulate_day(TOY_MIX_A, TOY_MIX_B, TOY_KAPPA, p_toy_scalar, sm.day_rng(5, d)) for d in range(3000)]
    stale = np.array([d.stale for d in days], dtype=np.float64)
    races = np.array([d.races for d in days], dtype=np.float64)
    model = fr.equilibrium_forks(TOY_MIX_A, TOY_MIX_B, TOY_KAPPA, TOY_TERMS)
    # day / E[race length] counts races as a renewal process; the race cut off at the end of the day
    # shifts the simulated count by under one race, hence the small absolute slack.
    assert abs(model["stale_per_day"] - stale.mean()) < 4 * stale.std() / math.sqrt(len(days)) + 0.5
    assert abs(model["races_per_day"] - races.mean()) < 4 * races.std() / math.sqrt(len(days)) + 1
    assert model["stale_per_race"] == pytest.approx(
        sum(model[f"stale_{cause}"] for cause in fr.CAUSES))
