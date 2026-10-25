import math

import numpy as np
import pytest

import buildpayoff as bp
import reference_model as ref


def test_budgets_and_work_at_2025_difficulty():
    W = bp.W_from_D(bp.D_2025)
    assert bp.kappa("nonce-only", W) == 51471
    assert bp.kappa("full-header", W) == 561770130060
    assert 2**32 / W == pytest.approx(8.395032e-15, rel=1e-6)


def test_nonce_only_exact_matches_approximation_at_2025_difficulty():
    W = bp.W_from_D(bp.D_2025)
    p = bp.success_prob("nonce-only", W)
    for k in (0, 1, 1000, 25735, 51471):
        approx = (2**32 / W) * math.sin((2 * k + 1) * math.asin(2.0**-16)) ** 2
        assert p(k) == pytest.approx(approx, rel=1e-12)


@pytest.mark.parametrize("n_q", [1, 6, 25, 200])
@pytest.mark.parametrize("kap", [10, 51471, 561770130060])
def test_grid_is_quadratic_floor_dedup_with_endpoints(n_q, kap):
    g = bp.grid(n_q, kap)
    expected = sorted({math.floor((1 - (1 - i / n_q) ** 2) * kap) for i in range(n_q + 1)})
    assert list(g) == expected
    assert g[0] == 0 and g[-1] == kap
    assert len(g) <= n_q + 1


def test_grid_worked_example():
    # i/n_q = 0, .5, 1 -> 1-(1-x)^2 = 0, .75, 1 -> floor(.75*10) = 7
    assert list(bp.grid(2, 10)) == [0, 7, 10]


W_2025 = ref.W_2025
GRID_N_Q = {1: 200, 2: 45, 3: 35, 4: 25}


def _random_profiles(rng, values, c, n):
    return np.array([[rng.choice(values) for _ in range(c)] for _ in range(n)], dtype=np.int64)


@pytest.mark.parametrize("regime", bp.REGIMES)
@pytest.mark.parametrize("c", [1, 2, 3, 4])
def test_matrices_match_reference_on_real_grids(regime, c):
    rng = np.random.default_rng(1000 * c + len(regime))
    kap = bp.kappa(regime, W_2025)
    values = bp.grid(GRID_N_Q[c], kap)
    S = _random_profiles(rng, values, c, 12)
    p_code = bp.success_prob(regime, W_2025)
    p_ref = ref.p_fn(regime, W_2025)
    for gamma in (0.0, 0.5, 1.0, float(rng.random())):
        A, B = bp.payoff_matrices(S, gamma, p_code)
        for r, a in enumerate(S):
            for col, b in enumerate(S):
                a_l, b_l = [int(x) for x in a], [int(x) for x in b]
                assert A[r, col] == pytest.approx(ref.alice_payoff(a_l, b_l, gamma, p_ref), rel=1e-12, abs=1e-300)
                assert B[r, col] == pytest.approx(ref.alice_payoff(b_l, a_l, 1 - gamma, p_ref), rel=1e-12, abs=1e-300)


TOY_W = 3000.0


def p_toy(k):
    """Toy success probability with large values, so every outcome has visible weight."""
    return (np.sin((2 * np.asarray(k, dtype=np.float64) + 1) * math.asin(1 / math.sqrt(TOY_W))) ** 2)[()]


def p_toy_scalar(k):
    return math.sin((2 * k + 1) * math.asin(1 / math.sqrt(TOY_W))) ** 2


def test_matrix_entries_match_brute_force_with_toy_p():
    rng = np.random.default_rng(7)
    values = [0, 5, 10, 15, 20, 25, 30]
    checked = 0
    for _ in range(400):
        c = int(rng.integers(1, 4))
        a = [int(rng.choice(values)) for _ in range(c)]
        b = [int(rng.choice(values)) for _ in range(c)]
        if ref.multi_tie(a, b):
            continue
        g = float(rng.random())
        u = bp.payoff_matrix([a], [b], g, p_toy)[0, 0]
        assert u == pytest.approx(ref.brute_force(a, b, g, p_toy_scalar), rel=1e-12, abs=1e-15)
        checked += 1
    assert checked > 300


@pytest.mark.parametrize("a,b", [(10, 20), (10, 10), (20, 10), (0, 30), (0, 0)])
def test_c1_closed_forms(a, b):
    g = 0.3
    pa, pb = p_toy_scalar(a), p_toy_scalar(b)
    if a <= b:
        expected = pa * (1 - pa) + g * pa * pa
    else:
        expected = pa * (1 - pb) + g * pb * pb
    assert bp.payoff_matrix([[a]], [[b]], g, p_toy)[0, 0] == pytest.approx(expected, rel=1e-13)


def _full_grid_strategies(n_q, c, kap):
    import itertools
    g = bp.grid(n_q, kap)
    return np.array([s for s in itertools.product(g, repeat=c) if sum(s) <= kap], dtype=np.int64)


@pytest.mark.parametrize("c", [2, 3])
@pytest.mark.parametrize("setting", ["nonce-only", "full-header", "toy"])
def test_full_matrices_are_bounded_and_symmetric(setting, c):
    if setting == "toy":
        kap, p = 30, p_toy
    else:
        kap, p = bp.kappa(setting, W_2025), bp.success_prob(setting, W_2025)
    S = _full_grid_strategies(6, c, kap)
    A, B = bp.payoff_matrices(S, 0.5, p)
    assert A.min() >= 0 and B.min() >= 0
    assert (A + B).max() <= 1 + 1e-12
    np.testing.assert_array_equal(B, A.T)
    A2, B2 = bp.payoff_matrices(S, 0.2, p)
    assert (A2 + B2).max() <= 1 + 1e-12


@pytest.mark.parametrize("regime", bp.REGIMES)
def test_feasible_strategy_counts_for_the_v2_runs(regime):
    # Counts from the 2026-10-25 audit (section B.12), identical in both regimes.
    kap = bp.kappa(regime, W_2025)
    for c, expected in {1: 201, 2: 484, 3: 1936, 4: 3094}.items():
        assert len(bp.feasible_strategies(bp.grid(GRID_N_Q[c], kap), c, kap)) == expected
