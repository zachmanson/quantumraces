import numpy as np

import buildpayoff as bp
from test_payoff import _full_grid_strategies, p_toy


def test_rows_and_columns_survive_independently():
    # Row 1 is strictly dominated for Alice; column 0 is strictly dominated for Bob.
    A = np.array([[3.0, 3.0], [1.0, 1.0]])
    B = np.array([[1.0, 2.0], [1.0, 2.0]])
    A2, B2, rows, cols = bp.eliminate_dominated(A, B)
    assert list(rows) == [0]
    assert list(cols) == [1]
    np.testing.assert_array_equal(A2, [[3.0]])
    np.testing.assert_array_equal(B2, [[2.0]])


def test_elimination_is_iterated():
    # Nothing is dominated for Alice at first. Bob's column 2 is dominated by column 0, and once it is
    # gone Alice's row 1 (better only against column 2) is dominated by row 0.
    A = np.array([[2.0, 2.0, 0.0],
                  [1.0, 1.0, 5.0]])
    B = np.array([[3.0, 1.0, 2.0],
                  [3.0, 4.0, 2.0]])
    _, _, rows, cols = bp.eliminate_dominated(A, B)
    assert list(rows) == [0]
    assert list(cols) == [0]


def test_weakly_dominated_strategies_are_kept():
    A = np.array([[2.0, 1.0], [2.0, 0.5]])   # row 0 is only weakly better (tie in column 0)
    B = np.array([[1.0, 1.0], [1.0, 1.0]])   # identical columns
    _, _, rows, cols = bp.eliminate_dominated(A, B)
    assert list(rows) == [0, 1]
    assert list(cols) == [0, 1]


def test_symmetric_game_keeps_the_same_strategies_for_both_players():
    # Under the first-finder rule B == A.T for every gamma, so Alice and Bob must keep the same strategies.
    S = _full_grid_strategies(6, 2, 30)
    A, B = bp.payoff_matrices(S, 0.6, p_toy)
    _, _, rows, cols = bp.eliminate_dominated(A, B)
    assert len(rows) < len(S)
    assert list(rows) == list(cols)
