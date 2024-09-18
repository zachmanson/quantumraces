import numpy as np
import math
from decimal import * 
import sys
import lemkehowson as lh
from util import cartesian
from typing import Callable
import quantecon.game_theory as gt

#==========
getcontext().prec = 30 #level of precision in Decimal 
#==========

def p(k: float, D: float, intvl: int) -> Decimal:
    return Decimal((math.sin(2 * ((k * intvl) + 1/2) * math.asin(1/np.sqrt(D))))**2)

def get_payoff(K: int, num_plays: int, D: float, intvl: int, gamma: Decimal, bob: bool = False) -> list:
    set_K = np.arange(0, K + 1) #change this to (0, K + 1) if I want to allow miners to not measure
    arrs = (set_K for i in range(num_plays))
    S = cartesian(arrs)

    dim = int(len(set_K)**num_plays)
    
    #A[0] = total matrix sum, A[1] ... A[n] = payoff matrices for nth chance alone
    A = [np.zeros((dim, dim), dtype = Decimal) for i in range(num_plays + 1)]

    #start populating all the matrices
    for play in range(1, num_plays + 1):
        for row in range(dim):
            for col in range(dim):
                element = get_element(K, gamma, D, intvl, S, row, col, play, dim, bob)
                A[play][row][col] = element
                A[0][row][col] += A[play][row][col]

    return A[0]

def get_prefactor(play: int, alice_strat: list, bob_strat: list, D: float, intvl: int, bob: bool) -> Decimal:
    strategy = bob_strat if bob else alice_strat
    prefactor = Decimal(p(strategy[play - 1], D, intvl))

    if play > 1:
        for c in range(play - 2, -1, -1):
            prefactor *= Decimal(1 - p(strategy[c], D, intvl))

    return prefactor        

def product_func(p: Callable, arr: list, D: float, intvl: int) -> Decimal:
    prod = 1
    for i in arr:
        prod *= Decimal((1 - p(i, D, intvl)))

    return prod


def get_case(K: float, gamma: Decimal, alice_strat: list, bob_strat: list, p: Callable, D: float, intvl: int, play: int, prefactor: Decimal, bob: bool = False) -> Decimal:
    if not bob:
        x = sum(alice_strat[:play])
        if x > K:
            return 0 
        elif x < bob_strat[0]:
            return product_func(p, [], D, intvl) + gamma/prefactor * (p(alice_strat[play-1], D, intvl))**2
        
        for i in range(len(bob_strat) - 1):
            if sum(bob_strat[:i+1]) < x < sum(bob_strat[:i+2]):
                return product_func(p, bob_strat[0:i+1], D, intvl) + gamma/prefactor *  (p(x - sum(bob_strat[:i+1]), D, intvl))**2
            elif x == sum(bob_strat[:i+1]):
                return product_func(p, bob_strat[0:i+2], D, intvl) + gamma/prefactor * p(alice_strat[play-1], D, intvl) * p(bob_strat[i], D, intvl)

        return product_func(p, bob_strat, D, intvl) 
    else:
        x = sum(bob_strat[:play])
        if x > K:
            return 0 
        elif x < alice_strat[0]:
            return product_func(p, [], D, intvl) + (1 - gamma/prefactor) * (p(bob_strat[play-1], D, intvl)**2)

        for i in range(len(alice_strat) - 1):
            if sum(alice_strat[:i+1]) < x < sum(alice_strat[:i+2]):
                return product_func(p, alice_strat[0:i+1], D, intvl) + (1 - gamma)/prefactor *  (p(x - sum(alice_strat[:i+1]), D, intvl))**2
            elif x == sum(alice_strat[:i+1]):
                return product_func(p, alice_strat[0:i+2], D, intvl) + (1 - gamma)/prefactor * p(bob_strat[play-1], D, intvl) * p(alice_strat[i], D, intvl)

        return product_func(p, alice_strat, D, intvl) 


def get_element(K: float, gamma: Decimal, D: float, intvl: int, S: np.ndarray, row: int, col: int, play: int, dim: int, bob: bool = False) -> Decimal:
    #get Alice's strategy and Bob's strategy by looking at the element of the cartesian product for this row and col
    row_strats, col_strats = S, S
    cartesian_element = [*row_strats[col], *col_strats[row]]
    strat_length = len(cartesian_element) // 2
    alice_strat = cartesian_element[strat_length:]
    bob_strat = cartesian_element[:strat_length]

    assert play <= strat_length, 'Only {} plays are allowed in this game, got {}'.format(strat_length, play)

    #first calculate the prefactor for the payoff matrix
    prefactor = get_prefactor(play, alice_strat, bob_strat, D, intvl, bob)
    element = Decimal(prefactor * get_case(K, gamma, alice_strat, bob_strat, p, D, intvl, play, prefactor, bob))
    return element


def print_results(result: np.ndarray, player: str, K: int, num_plays: int, intvl: int) -> None:
    for i, value in enumerate(result):
        if abs(value) != 0.0:
            set_K = np.arange(0, K + 1)
            cart_prod = cartesian((set_K for x in range(num_plays)))
            strat = [intvl * x for x in cart_prod[i]]
            print('{} {} {}'.format(player, strat, value))

    return 


def get_nash_eq_old(A: list, B: list, K: int, num_plays: int, intvl: int) -> None:
    mat_dim = len(A[0])
    tableaux, basic_vars = lh.create_tableau(A, B)
    Crange = basic_vars
    nash_eqs = []
    with open('output.txt', 'w') as f:
        sys.stdout = f

        for i in range(mat_dim):
            eq = lh.Lemke_Howson(tableaux, basic_vars, Crange, init_pivot = i)

            if not ( 
                    any((np.allclose(eq[0], item[0]) and np.allclose(eq[1], item[1]) for item in nash_eqs))
                    ):
                nash_eqs.append(eq)
                print_results(np.round(eq[0], 20), 'Alice', K, num_plays, intvl)
                print_results(np.round(eq[1], 20), 'Bob', K, num_plays, intvl)
                print('------')
             
    return

def get_nash_eq(A: np.ndarray, B: np.ndarray, K: int, num_plays: int, intvl: int) -> None:
    mat_dim = len(A[0])
    g = gt.NormalFormGame((mat_dim, mat_dim))
    for row in range(mat_dim):
        for col in range(mat_dim):
            g[row, col] =A[row][col], B[row][col]

    nash_eqs = []
    with open('output.txt', 'w') as f:
        sys.stdout = f

        for i in range(mat_dim):
            eq = gt.lemke_howson(g, init_pivot = i)

            if len(nash_eqs) >= 1:
                break

            if not(any((np.allclose(eq[0], item[0]) and np.allclose(eq[1], item[1]) for item in nash_eqs))):
                nash_eqs.append(eq)
                print_results(np.round(eq[0], 3), 'Alice', K, num_plays, intvl)
                print_results(np.round(eq[1], 3), 'Bob', K, num_plays, intvl)
                print('-------------')
                
    return 


def main():
    K = 10 #number of pure strategies
    num_plays = 3 #number of plays
    D = 82047028459932.62
    #D = 52328312063444
    max_K = np.floor(np.pi / 4 * np.sqrt(D))
    intvl = max_K // K
    gamma = 0.5
    
    A = get_payoff(K, num_plays, D, intvl, Decimal(gamma))
    mat_dim = len(A[0])
    B = get_payoff(K, num_plays, D, intvl, Decimal(gamma), bob = True)

    print('Payoff matrices created!')

    get_nash_eq(A, B, K, num_plays, intvl)

if __name__ == '__main__':
    main()
