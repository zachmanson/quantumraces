import numpy as np
from decimal import * 
import sys
import lemkehowson as lh
from util import cartesian

#==========
getcontext().prec = 15 #level of precision in Decimal 
#==========

def p(k: float, D: float, intvl: int) -> Decimal:
    theta = float(np.arcsin(1/ np.sqrt(D)))
    return Decimal((np.sin(2*(k * intvl + 1) * theta))**2)

def get_payoff(K: int, num_plays: int) -> list:
    set_K = np.arange(1, K + 1) #change this to (0, K + 1) if I want to allow miners to not measure
    arrs = (set_K for i in range(num_plays))
    S = cartesian(arrs)

    dim = int(len(set_K)**num_plays)
    
    #A[0] = total matrix sum, A[1] ... A[n] = payoff matrices for nth chance alone
    A = [np.zeros((dim, dim), dtype = Decimal) for i in range(num_plays + 1)]

    #start populating all the matrices
    for play in range(1, num_plays + 1):
        for col in range(dim):
            for row in range(dim):
                element = get_element(S, col, row, play, dim)
                A[play][col][row] = element
                A[0][col][row] += A[play][col][row]

    return A[0]

def get_element(S: np.ndarray, col: int, row: int, play: int, dim: int, bob = False) -> Decimal:
    return 1
    

print(get_payoff(2, 2))
