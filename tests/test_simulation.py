from collections import Counter

import numpy as np
import pytest

import simulate_mining as sm


def p_only(*succeeding):
    """Deterministic p: a measurement after k iterations succeeds iff k is listed."""
    return lambda k: 1.0 if k in succeeding else 0.0


def race(alice, bob, classical_tick, p, start_tick=0):
    rng = np.random.default_rng(0)
    return sm.simulate_race(alice, bob, start_tick, classical_tick, p, rng, baseline_stale=0.0)


def test_classical_block_with_a_failed_measurement_makes_the_other_miner_respond():
    # Alice measures at tick 10 and fails; Bob last measured at tick 3 and responds with 7 iterations.
    out = race((10,), (3, 20), classical_tick=10, p=p_only(7))
    assert Counter(out.finders) == Counter(["Classical", "Bob"])
    assert out.stale == 1
    assert out.end_tick == 10
    assert out.classical_ended


def test_three_coincident_blocks_are_all_counted():
    out = race((10,), (10,), classical_tick=10, p=p_only(10))
    assert Counter(out.finders) == Counter(["Alice", "Bob", "Classical"])
    assert out.stale == 2


def test_classical_block_and_quantum_success_trigger_a_response():
    out = race((10,), (3, 30), classical_tick=10, p=p_only(10, 7))
    assert Counter(out.finders) == Counter(["Alice", "Bob", "Classical"])
    assert out.stale == 2


def test_exhausted_miner_cannot_respond():
    out = race((10,), (3,), classical_tick=None, p=p_only(10, 7))
    assert out.finders == ["Alice"]
    assert out.stale == 0


def test_lone_classical_block_makes_both_miners_respond_with_accumulated_iterations():
    out = race((10,), (12,), classical_tick=5, p=p_only(5))
    assert Counter(out.finders) == Counter(["Alice", "Bob", "Classical"])


def test_race_clock_starts_at_the_start_tick():
    out = race((10,), (5, 20), classical_tick=None, p=p_only(10), start_tick=1000)
    assert out.finders == ["Alice"] and out.end_tick == 1010


def test_race_with_no_block_and_no_classical_network_ends_empty():
    out = race((10, 5), (20,), classical_tick=None, p=p_only())
    assert out.finders == [] and out.end_tick is None


def test_baseline_fork_marks_a_classical_block_stale():
    out = sm.simulate_race((), (), 0, 50, p_only(), np.random.default_rng(0), baseline_stale=1.0)
    assert out.finders == ["Classical"] and out.stale == 1


# ---------------------------------------------------------------- simulation == payoff matrices
import buildpayoff as bp
import reference_model as ref
from test_payoff import p_toy, p_toy_scalar

CONSISTENCY_PROFILES = [
    ((10, 20), (15, 15)),          # tie at 30
    ((0, 25), (10, 5)),            # zero-iteration first measurement
    ((30,), (5,)),                 # Bob exhausted after tick 5
    ((5, 5, 20), (20, 0, 10)),     # Bob measures twice at tick 20; tie at 30
    ((10, 10), (10, 10)),          # every measurement tied
    ((0, 0, 30), (12, 12, 6)),     # Alice measures twice at tick 0
]
N_RACES = 1_000_000


@pytest.mark.slow
@pytest.mark.parametrize("a,b", CONSISTENCY_PROFILES)
def test_race_frequencies_match_payoff_entries(a, b):
    assert not ref.multi_tie(list(a), list(b))
    rng = np.random.default_rng(abs(hash((a, b))) % 2**32)
    counts = Counter()
    for _ in range(N_RACES):
        f = set(sm.simulate_race(a, b, 0, None, p_toy_scalar, rng, baseline_stale=0.0).finders)
        counts["fork" if f == {"Alice", "Bob"} else "alice" if f == {"Alice"} else "bob" if f == {"Bob"} else "none"] += 1

    alice0 = bp.payoff_matrix([a], [b], 0.0, p_toy)[0, 0]
    alice1 = bp.payoff_matrix([a], [b], 1.0, p_toy)[0, 0]
    bob0 = bp.payoff_matrix([b], [a], 0.0, p_toy)[0, 0]
    report = {}
    for key, expected in (("alice", alice0), ("bob", bob0), ("fork", alice1 - alice0)):
        freq = counts[key] / N_RACES
        se = max(np.sqrt(expected * (1 - expected) / N_RACES), 1 / N_RACES)
        report[key] = (freq, expected, (freq - expected) / se)
    print(f"\n{a} vs {b}: " + ", ".join(f"{k}: freq={f:.5f} model={e:.5f} z={z:+.2f}" for k, (f, e, z) in report.items()))
    for key, (freq, expected, z) in report.items():
        assert abs(z) < 4, f"{key}: freq {freq} vs model {expected} (z = {z:.2f})"


# ---------------------------------------------------------------- simulated days
NO_QUANTUM = {(): 1.0}


def test_without_quantum_miners_the_stale_rate_is_the_classical_baseline():
    blocks = stale = 0
    for day in range(3000):
        r = sm.simulate_day(NO_QUANTUM, NO_QUANTUM, 51471, p_only(), sm.day_rng(11, day))
        blocks += r.blocks
        stale += r.stale
        assert r.classical_ended == r.races
    expected = sm.CLASSICAL_STALE_RATE * blocks
    assert abs(stale - expected) < 4 * np.sqrt(expected * (1 - sm.CLASSICAL_STALE_RATE))
    # Exponential(600 s) arrivals over 86400 s: 144 blocks per day on average
    assert abs(blocks / 3000 - 144) < 4 * np.sqrt(144 / 3000)


def test_days_are_reproducible_from_the_master_seed():
    mixed = {(10, 20): 0.4, (30, 0): 0.6}
    run = lambda seed, day: sm.simulate_day(mixed, mixed, 30, p_toy_scalar, sm.day_rng(seed, day))
    assert run(5, 17) == run(5, 17)
    assert [run(5, d) for d in range(5)] != [run(6, d) for d in range(5)]


def test_classical_arrivals_use_the_integer_clock_at_full_header_scale():
    # Both miners measure once with the full budget (p(kappa) ~ 1), i.e. 600 s after the race starts.
    # The race ends classically iff Exponential(600 s) < 600 s: probability 1 - 1/e.
    W = ref.W_2025
    kap = bp.kappa("full-header", W)
    p = bp.success_prob("full-header", W)
    races = classical = 0
    for day in range(10):
        r = sm.simulate_day({(kap,): 1.0}, {(kap,): 1.0}, kap, lambda k: float(p(k)), sm.day_rng(3, day))
        races += r.races
        classical += r.classical_ended
    share = 1 - np.exp(-1)
    assert abs(classical / races - share) < 4 * np.sqrt(share * (1 - share) / races)
