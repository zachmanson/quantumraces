import math

import numpy as np
import pytest

import buildpayoff as bp
import util
from test_payoff import p_toy, p_toy_scalar


def test_written_equilibrium_reads_back_exactly(tmp_path):
    alice = {(0, 7, 23): 0.25, (5, 5, 5): 0.75}
    bob = {(30, 0, 0): 1.0}
    path = tmp_path / "eq.txt"
    util.write_equilibrium(path, alice, bob)
    assert util.read_equilibrium(path) == (alice, bob)


def test_reading_a_file_with_two_equilibria_is_an_error(tmp_path):
    path = tmp_path / "two.txt"
    util.write_equilibrium(path, {(1,): 1.0}, {(1,): 1.0})
    with open(path, "a") as f:
        f.write("Alice [2] 1.0\nBob [2] 1.0\n-------------\n")
    with pytest.raises(ValueError):
        util.read_equilibrium(path)


def test_equilibrium_file_names_follow_stop_after(tmp_path):
    eqs = [({(1,): 1.0}, {(2,): 1.0}), ({(3,): 1.0}, {(4,): 1.0})]
    single = util.write_equilibria(tmp_path / "nash_c1", eqs[:1], stop_after=1)
    assert [p.name for p in single] == ["nash_c1.txt"]
    multi = util.write_equilibria(tmp_path / "nash_c1", eqs, stop_after=2)
    assert [p.name for p in multi] == ["nash_c1_eq1.txt", "nash_c1_eq2.txt"]
    assert util.read_equilibrium(multi[1]) == eqs[1]


def test_expected_payoff_of_pure_c1_profile():
    g = 0.5
    pa, pb = p_toy_scalar(10), p_toy_scalar(20)
    alice_ep, bob_ep = bp.expected_payoffs({(10,): 1.0}, {(20,): 1.0}, g, p_toy)
    assert alice_ep == pytest.approx(pa * (1 - pa) + g * pa * pa, rel=1e-13)
    assert bob_ep == pytest.approx(pb * (1 - pa) + (1 - g) * pa * pa, rel=1e-13)


def test_expected_payoff_gives_gamma_to_bob_when_he_finds_first():
    # Bob measures first at 10; if Alice's response at 20 also succeeds, Bob's block wins w.p. gamma.
    g = 0.6
    pa, pb = p_toy_scalar(20), p_toy_scalar(10)
    alice_ep, bob_ep = bp.expected_payoffs({(20,): 1.0}, {(10,): 1.0}, g, p_toy)
    assert alice_ep == pytest.approx(pa * (1 - pb) + (1 - g) * pb * pb, rel=1e-13)
    assert bob_ep == pytest.approx(pb * (1 - pb) + g * pb * pb, rel=1e-13)


def test_expected_payoff_equals_sigma_A_sigma_on_the_matrices():
    S = np.array([[0, 30], [10, 10], [25, 5]])
    sa = np.array([0.2, 0.5, 0.3])
    sb = np.array([0.6, 0.0, 0.4])
    A, B = bp.payoff_matrices(S, 0.3, p_toy)
    alice = {tuple(int(x) for x in s): w for s, w in zip(S, sa) if w > 0}
    bob = {tuple(int(x) for x in s): w for s, w in zip(S, sb) if w > 0}
    alice_ep, bob_ep = bp.expected_payoffs(alice, bob, 0.3, p_toy)
    assert alice_ep == pytest.approx(sa @ A @ sb, rel=1e-13)
    assert bob_ep == pytest.approx(sa @ B @ sb, rel=1e-13)


def test_solver_finds_the_mixed_equilibrium_of_matching_pennies():
    A = np.array([[1.0, 0.0], [0.0, 1.0]])
    B = 1 - A
    eqs = bp.solve_nash(A, B, stop_after=1)
    assert len(eqs) == 1
    sa, sb = eqs[0]
    np.testing.assert_allclose(sa, [0.5, 0.5])
    np.testing.assert_allclose(sb, [0.5, 0.5])


def test_measurement_schedule_averages_iterations_and_skips_leading_zeros_for_the_first_measurement():
    # kappa = 100. Mean schedule: (0.5*0 + 0.25*20 + 0.25*40, 0.5*50 + 0.25*30 + 0.25*0) / 100.
    # First measurement at a non-zero count: 50, 20, 40 -> 0.5*50 + 0.25*20 + 0.25*40 = 40.
    mixed = {(0, 50): 0.5, (20, 30): 0.25, (40, 0): 0.25}
    schedule, first = bp.measurement_schedule(mixed, 100)
    assert schedule == pytest.approx([0.15, 0.325])
    assert first == pytest.approx(0.40)
