import numpy as np
import lemkehowson as lh
import sys
from decimal import *
from util import cartesian

# ===================
getcontext().prec = 15
# ===================



def p_i(t: float, D: float, intvl: int) -> Decimal:
    theta = float(np.arcsin(1 / np.sqrt(D)))
    return Decimal((np.sin(2*(t * intvl + 1) * theta))**2)


def get_payoff(K: int, num_plays: int, D: float, intvl: int, is_bob: bool) -> list:
    #first get all of the strategies from the cartesian product to index the matrix
    set_K = np.arange(0, K + 1)
    arrs = (set_K for i in range(num_plays))
    S = cartesian(arrs)

    #dimension of the payoff matrix
    dim = int(len(set_K)**num_plays)

    #initialize the payoff matrices. There will be a separate one for each play, 
    A = [np.zeros((dim, dim), dtype = Decimal) for i in range(num_plays + 1)]

    for play in range(1, num_plays + 1):
        for col in range(dim):
            for row in range(dim):
                element = get_element(S, col, row, play, dim, D, intvl, is_bob)
                A[play][col][row] = element
                A[0][col][row] = A[0][col][row] + A[play][col][row]
    return A[0]

def get_element(S, col, row, play, dim, D, intvl, is_bob):
    row_strats, col_strats = S, S
    cart = [*row_strats[col], *col_strats[row]]
    strat_length = len(cart) // 2
    alice_strat = cart[:strat_length]
    bob_strat = cart[strat_length:]

    assert play <= strat_length, 'Only {} plays are allowed in this game, got {}'.format(strat_length, play)

    prefactor = p_i(alice_strat[play - 1], D, intvl)
    if play > 1:
        c = play - 2 
        while c >= 0:
            prefactor *= Decimal(1 - p_i(alice_strat[c], D, intvl))
            c -= 1

    element = Decimal(prefactor * get_interval())

    return element

def get_interval():
    return 1



def main(N, D, num_plays, K, max_K, gamma):
    intvl = max_K // K
    A = get_payoff(K, num_plays, D, intvl, is_bob = False)
    print(A)


    return

if __name__ == "__main__":
    N = 2**(256)
    D = 1e10
    num_plays = 2
    K = 20
    max_K = np.floor(np.pi/4 * np.sqrt(D))
    gamma = 0.5
    main(N, D, num_plays, K, max_K, gamma)
