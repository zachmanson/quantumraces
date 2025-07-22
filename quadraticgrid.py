import numpy as np
import math
import sys
import pygambit
from util import cartesian
from typing import Callable
from functools import lru_cache

#==========
#==========

@lru_cache(maxsize=None)
def p(k: float, D: float, intvl: int) -> np.float64:
    return np.float64((math.sin(2 * ((k * intvl) + 1/2) * math.asin(1/np.sqrt(D))))**2)

def create_quadratic_grid(K: int, max_K: float, clustering_factor: float = 1.0) -> np.ndarray:
    # Create an evenly spaced grid from 0 to 1
    linear_grid = np.linspace(0, 1, K + 1)
    
    # Apply quadratic transform to cluster points near 1 (which will map to max_K)
    # Using 1 - (1-x)^2 transformation which clusters points near 1
    quadratic_grid = 1 - (1 - linear_grid)**clustering_factor
    
    # Scale to the range [0, max_K]
    scaled_grid = quadratic_grid * max_K
    
    # Make sure values are integers (number of iterations must be an integer)
    return np.round(scaled_grid).astype(int)

def grid_to_iterations(grid_point: int, grid: np.ndarray) -> int:
    """
    Converts a grid index to the corresponding number of Grover iterations.
    
    Args:
        grid_point: Index in the grid (0 to K)
        grid: The quadratic grid array
        
    Returns:
        The number of Grover iterations
    """
    return grid[grid_point]

def get_payoff(K: int, num_plays: int, D: float, grid: np.ndarray, gamma: np.float64, bob: bool = False) -> list:
    set_K = np.arange(0, K + 1)
    arrs = (set_K for i in range(num_plays))
    S = cartesian(arrs)

    dim = int(len(set_K)**num_plays)
    
    #A[0] = total matrix sum, A[1] ... A[n] = payoff matrices for nth chance alone
    A = [np.zeros((dim, dim), dtype=np.float64) for i in range(num_plays + 1)]

    #start populating all the matrices
    for play in range(1, num_plays + 1):
        for row in range(dim):
            for col in range(dim):
                element = get_element(K, gamma, D, grid, S, row, col, play, dim, bob)
                A[play][row][col] = element
                A[0][row][col] += A[play][row][col]

    return A[0]

def get_prefactor(play: int, alice_strat: list, bob_strat: list, D: float, grid: np.ndarray, bob: bool) -> np.float64:
    strategy = bob_strat if bob else alice_strat
    iterations = grid_to_iterations(strategy[play - 1], grid)
    prefactor = np.float64(p(iterations, D, 1))  

    if play > 1:
        for c in range(play - 2, -1, -1):
            iterations = grid_to_iterations(strategy[c], grid)
            prefactor *= np.float64(1 - p(iterations, D, 1))

    return prefactor        

def product_func(p: Callable, arr: list, D: float, grid: np.ndarray) -> np.float64:
    prod = 1
    for i in arr:
        iterations = grid_to_iterations(i, grid)
        prod *= np.float64((1 - p(iterations, D, 1)))  

    return np.float64(prod)

def get_case(K: float, gamma: np.float64, alice_strat: list, bob_strat: list, p: Callable, D: float, grid: np.ndarray, play: int, prefactor: np.float64, bob: bool = False) -> np.float64:
    if not bob:
        x = sum(alice_strat[:play])
        if x > K:
            return np.float64(0)
        elif x < bob_strat[0]:
            return product_func(p, [], D, grid) + gamma/prefactor * (p(grid_to_iterations(alice_strat[play-1], grid), D, 1))**2
        
        for i in range(len(bob_strat) - 1):
            if sum(bob_strat[:i+1]) < x < sum(bob_strat[:i+2]):
                return product_func(p, bob_strat[0:i+1], D, grid) + gamma/prefactor * (p(grid_to_iterations(x - sum(bob_strat[:i+1]), grid), D, 1))**2
            elif x == sum(bob_strat[:i+1]):
                return product_func(p, bob_strat[0:i+2], D, grid) + gamma/prefactor * p(grid_to_iterations(alice_strat[play-1], grid), D, 1) * p(grid_to_iterations(bob_strat[i], grid), D, 1)

        return product_func(p, bob_strat, D, grid) 
    else:
        x = sum(bob_strat[:play])
        if x > K:
            return np.float64(0)
        elif x < alice_strat[0]:
            return product_func(p, [], D, grid) + (1 - gamma/prefactor) * (p(grid_to_iterations(bob_strat[play-1], grid), D, 1)**2)

        for i in range(len(alice_strat) - 1):
            if sum(alice_strat[:i+1]) < x < sum(alice_strat[:i+2]):
                return product_func(p, alice_strat[0:i+1], D, grid) + (1 - gamma)/prefactor * (p(grid_to_iterations(x - sum(alice_strat[:i+1]), grid), D, 1))**2
            elif x == sum(alice_strat[:i+1]):
                return product_func(p, alice_strat[0:i+2], D, grid) + (1 - gamma)/prefactor * p(grid_to_iterations(bob_strat[play-1], grid), D, 1) * p(grid_to_iterations(alice_strat[i], grid), D, 1)

        return product_func(p, alice_strat, D, grid) 

def get_element(K: float, gamma: np.float64, D: float, grid: np.ndarray, S: np.ndarray, row: int, col: int, play: int, dim: int, bob: bool = False) -> np.float64:
    #get Alice's strategy and Bob's strategy by looking at the element of the cartesian product for this row and col
    row_strats, col_strats = S, S
    cartesian_element = [*row_strats[col], *col_strats[row]]
    strat_length = len(cartesian_element) // 2
    alice_strat = cartesian_element[strat_length:]
    bob_strat = cartesian_element[:strat_length]

    assert play <= strat_length, 'Only {} plays are allowed in this game, got {}'.format(strat_length, play)

    #first calculate the prefactor for the payoff matrix
    prefactor = get_prefactor(play, alice_strat, bob_strat, D, grid, bob)
    element = np.float64(prefactor * get_case(K, gamma, alice_strat, bob_strat, p, D, grid, play, prefactor, bob))

    #print('Alice strategy:', alice_strat, 'Bob strategy:', bob_strat, 'play:', play, 'element:', element)
    return element

def print_results(result: list, player: str, K: int, num_plays: int, grid: np.ndarray) -> None:
    set_K = np.arange(0, K + 1)
    cart_prod = cartesian((set_K for x in range(num_plays)))
    for i, value in enumerate(result):
        if abs(value) != 0.0:
            # Convert grid indices to actual iteration counts
            strat = [grid_to_iterations(x, grid) for x in cart_prod[i]]
            print('{} {} {}'.format(player, strat, value))

    return 

def get_nash_eq_pygambit(A: np.ndarray, B: np.ndarray, K: int, num_plays: int, grid: np.ndarray) -> None:
    A_float = A
    B_float = B
    
    print(f"Matrix A min: {np.min(A_float)}, max: {np.max(A_float)}")
    print(f"Matrix B min: {np.min(B_float)}, max: {np.max(B_float)}")

    game = pygambit.Game.from_arrays(A_float, B_float)
    
    # Add player labels
    game.players[0].label = "Alice"
    game.players[1].label = "Bob"
    
    # Find a Nash equilibrium using Gambit
    # Using LCP solver which is equivalent to Lemke-Howson
    results = pygambit.nash.lcp_solve(game, rational=True, stop_after= 1)
    
    with open('output_gambit.txt', 'w') as f:
        sys.stdout = f
        for eq in results.equilibria:
            alice_strat = eq['Alice']
            alice_probs = [float(p) for _, p in alice_strat]
            
            bob_strat = eq['Bob']
            bob_probs = [float(p) for _, p in bob_strat]
            
            print_results(alice_probs, 'Alice', K, num_plays, grid)
            print_results(bob_probs, 'Bob', K, num_plays, grid)
            print('-------------')

    return

def get_payoff_element(alice_strat: list, bob_strat: list, num_plays: int, K: float, D: float, grid: np.ndarray, gamma: np.float64, bob: bool = False) -> np.float64:
    payoff = np.float64(0)
    for play in range(1, num_plays + 1):
        prefactor = get_prefactor(play, alice_strat, bob_strat, D, grid, bob)
        element = np.float64(prefactor * get_case(K, gamma, alice_strat, bob_strat, p, D, grid, play, prefactor, bob))
        payoff += element
    return payoff

def test_quadratic_grid(K: int, max_K: float, clustering_factor: float = 1.0) -> None:
    """
    Test function to verify the quadratic grid behaves as expected.
    """
    grid = create_quadratic_grid(K, max_K, clustering_factor)
    
    # Print the grid points and their spacing
    print("Grid points:")
    print(grid)
    
    # Calculate the differences between consecutive grid points
    differences = np.diff(grid)
    print("\nDifferences between consecutive points:")
    print(differences)
    
    # Verify that spacing is smaller near max_K (end of the grid)
    if all(differences[i] <= differences[i+1] for i in range(len(differences)-1)):
        print("\nVerification FAILED: Grid spacing is not decreasing toward max_K")
    else:
        print("\nVerification PASSED: Grid spacing is generally decreasing toward max_K")
    
    # Plot the grid distribution if matplotlib is available
    try:
        import matplotlib.pyplot as plt
        plt.figure(figsize=(10, 6))
        plt.plot(range(len(grid)), grid, 'o-')
        plt.title(f"Quadratic Grid Distribution (clustering_factor={clustering_factor})")
        plt.xlabel("Grid Index")
        plt.ylabel("Grover Iterations")
        plt.grid(True)
        plt.savefig("quadratic_grid_distribution.png")
        print("\nGrid distribution plot saved as 'quadratic_grid_distribution.png'")
    except ImportError:
        print("\nMatplotlib not available. Grid plotting skipped.")

def main():
    K = 10 #number of pure strategies
    num_plays = 2 #number of plays
    D = 82047028459932.62
    #D = 52328312063444
    max_K = np.floor(np.pi / 4 * np.sqrt(D))

    clustering_factor = 2.0
    grid = create_quadratic_grid(K, max_K, clustering_factor)
    
    test_quadratic_grid(K, max_K, clustering_factor)
    
    gamma = 0.5
    
    A = get_payoff(K, num_plays, D, grid, np.float64(gamma))
    B = get_payoff(K, num_plays, D, grid, np.float64(gamma), bob=True)

    print(A, B)

    print("Payoff matrices created!")
    
    get_nash_eq_pygambit(A, B, K, num_plays, grid)

if __name__ == '__main__':
    main()