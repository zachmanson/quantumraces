import numpy as np
import math
import sys
import pygambit
from util import cartesian
from typing import Callable
from functools import lru_cache
import matplotlib.pyplot as plt


class BuildPayoff:
    def __init__(self, K: int, num_plays: int, D: float, clustering_factor: float = 1.0, gamma: float = 0.5, beta: float = 1.0, out_fname = 'output.txt', scale_with_D: bool = False):
        self.K = K
        self.num_plays = num_plays
        self.D = D
        self.scale_with_D = scale_with_D

        if self.scale_with_D:
            self.max_K = np.floor(np.pi / 4 * np.sqrt(self.D))
        else:
            self.max_K = np.floor(np.pi / 4 * np.sqrt(min(self.D, 2**32)))
            
        print(f"Using max_K: {self.max_K}")
        self.clustering_factor = clustering_factor
        self.gamma = np.float64(gamma)
        self.beta = beta
        self.grid = self.create_quadratic_grid()
        self.out_fname = out_fname

    @staticmethod
    @lru_cache(maxsize=None)
    def p(k: float, D: float, intvl: int) -> np.float64:
        return np.float64((math.sin(2 * ((k * intvl) + 1/2) * math.asin(1/np.sqrt(D))))**2)

    def create_quadratic_grid(self) -> np.ndarray:
        linear_grid = np.linspace(0, 1, self.K + 1)
        quadratic_grid = 1 - (1 - linear_grid)**self.clustering_factor
        scaled_grid = quadratic_grid * self.max_K
        return np.round(scaled_grid).astype(int)

    def grid_to_iterations(self, grid_point: int) -> int:
        return self.grid[grid_point]

    def get_payoff(self, bob: bool = False) -> list:
        set_K = np.arange(0, self.K + 1)
        arrs = (set_K for i in range(self.num_plays))
        S = cartesian(arrs)

        dim = int(len(set_K)**self.num_plays)
        
        #A[0] = total matrix sum, A[1] ... A[n] = payoff matrices for nth chance alone
        A = [np.zeros((dim, dim), dtype=np.float64) for i in range(self.num_plays + 1)]

        #start populating all the matrices
        for play in range(1, self.num_plays + 1):
            for row in range(dim):
                for col in range(dim):
                    element = self.get_element(S, row, col, play, dim, bob)
                    A[play][row][col] = element
                    A[0][row][col] += A[play][row][col]

        # Clean up any NaN or inf values in the final matrix
        A[0] = np.nan_to_num(A[0], nan=0.0, posinf=0.0, neginf=0.0)
        return A[0]

    def get_prefactor(self, play: int, alice_strat: list, bob_strat: list, bob: bool) -> np.float64:
        strategy = bob_strat if bob else alice_strat
        iterations = self.grid_to_iterations(strategy[play - 1])
        prefactor = np.float64(self.p(iterations, self.D, 1))  

        if play > 1:
            for c in range(play - 2, -1, -1):
                iterations = self.grid_to_iterations(strategy[c])
                prefactor *= np.float64(1 - self.p(iterations, self.D, 1))

        return prefactor

    def product_func(self, arr: list) -> np.float64:
        prod = 1
        for i in arr:
            iterations = self.grid_to_iterations(i)
            prod *= np.float64((1 - self.p(iterations, self.D, 1)))  

        return np.float64(prod)

    def get_case(self, alice_strat: list, bob_strat: list, play: int, prefactor: np.float64, bob: bool = False) -> np.float64:
        # Handle zero prefactor case to avoid division by zero
        if prefactor == 0:
            return np.float64(0)
            
        # Calculate maximum allowed iterations based on beta
        max_allowed_iterations = self.beta * self.max_K
        
        if not bob:
            # Convert strategy indices to actual iterations using the grid
            alice_iterations_total = sum(self.grid_to_iterations(strat_idx) for strat_idx in alice_strat[:play])
            
            # Check if total iterations exceed the maximum allowed
            if alice_iterations_total > max_allowed_iterations:
                return np.float64(0)
                
            # Continue with existing logic
            if alice_iterations_total < self.grid_to_iterations(bob_strat[0]):
                return self.product_func([]) + self.gamma/prefactor * (self.p(self.grid_to_iterations(alice_strat[play-1]), self.D, 1))**2
            
            for i in range(len(bob_strat) - 1):
                bob_iterations_sum = sum(self.grid_to_iterations(strat_idx) for strat_idx in bob_strat[:i+1])
                next_bob_iterations_sum = sum(self.grid_to_iterations(strat_idx) for strat_idx in bob_strat[:i+2])
                
                if bob_iterations_sum < alice_iterations_total < next_bob_iterations_sum:
                    return self.product_func(bob_strat[0:i+1]) + self.gamma/prefactor * (self.p(self.grid_to_iterations(alice_strat[play-1]), self.D, 1))**2
                elif alice_iterations_total == bob_iterations_sum:
                    return self.product_func(bob_strat[0:i+2]) + self.gamma/prefactor * self.p(self.grid_to_iterations(alice_strat[play-1]), self.D, 1) * self.p(self.grid_to_iterations(bob_strat[i]), self.D, 1)

            return self.product_func(bob_strat) 
        else:
            # Convert strategy indices to actual iterations using the grid
            bob_iterations_total = sum(self.grid_to_iterations(strat_idx) for strat_idx in bob_strat[:play])
            
            # Check if total iterations exceed the maximum allowed
            if bob_iterations_total > max_allowed_iterations:
                return np.float64(0)
                
            # Continue with existing logic
            if bob_iterations_total < self.grid_to_iterations(alice_strat[0]):
                return self.product_func([]) + (1 - self.gamma)/prefactor * (self.p(self.grid_to_iterations(bob_strat[play-1]), self.D, 1)**2)

            for i in range(len(alice_strat) - 1):
                alice_iterations_sum = sum(self.grid_to_iterations(strat_idx) for strat_idx in alice_strat[:i+1])
                next_alice_iterations_sum = sum(self.grid_to_iterations(strat_idx) for strat_idx in alice_strat[:i+2])
                
                if alice_iterations_sum < bob_iterations_total < next_alice_iterations_sum:
                    return self.product_func(alice_strat[0:i+1]) + (1 - self.gamma)/prefactor * (self.p(self.grid_to_iterations(bob_strat[play-1]), self.D, 1))**2
                elif bob_iterations_total == alice_iterations_sum:
                    return self.product_func(alice_strat[0:i+2]) + (1 - self.gamma)/prefactor * self.p(self.grid_to_iterations(bob_strat[play-1]), self.D, 1) * self.p(self.grid_to_iterations(alice_strat[i]), self.D, 1)

            return self.product_func(alice_strat)

    def get_element(self, S: np.ndarray, row: int, col: int, play: int, dim: int, bob: bool = False) -> np.float64:
        #get Alice's strategy and Bob's strategy by looking at the element of the cartesian product for this row and col
        row_strats, col_strats = S, S
        cartesian_element = [*row_strats[col], *col_strats[row]]
        strat_length = len(cartesian_element) // 2
        alice_strat = cartesian_element[strat_length:]
        bob_strat = cartesian_element[:strat_length]

        assert play <= strat_length, 'Only {} plays are allowed in this game, got {}'.format(strat_length, play)

        #first calculate the prefactor for the payoff matrix
        prefactor = self.get_prefactor(play, alice_strat, bob_strat, bob)
        
        # Prevent calculations with zero prefactor
        if prefactor == 0:
            return np.float64(0)
            
        element = np.float64(prefactor * self.get_case(alice_strat, bob_strat, play, prefactor, bob))
        
        # Clean up any invalid values
        if np.isnan(element) or np.isinf(element):
            return np.float64(0)
            
        return element

    def print_results(self, result: list, player: str) -> None:
        set_K = np.arange(0, self.K + 1)
        cart_prod = cartesian((set_K for x in range(self.num_plays)))
        for i, value in enumerate(result):
            if abs(value) != 0.0:
                # Convert grid indices to actual iteration counts
                strat = [self.grid_to_iterations(x) for x in cart_prod[i]]
                print('{} {} {}'.format(player, strat, value))

        return 

    def get_nash_eq_pygambit(self, A: np.ndarray, B: np.ndarray) -> None:
        # Ensure matrices have valid values
        A_float = np.nan_to_num(A, nan=0.0, posinf=0.0, neginf=0.0)
        B_float = np.nan_to_num(B, nan=0.0, posinf=0.0, neginf=0.0)
        
        # Check for any remaining issues in the matrices
        if np.any(np.isnan(A_float)) or np.any(np.isinf(A_float)) or np.any(np.isnan(B_float)) or np.any(np.isinf(B_float)):
            print("Warning: Matrices still contain invalid values after cleaning.")
            
        print(f"Matrix A min: {np.min(A_float)}, max: {np.max(A_float)}")
        print(f"Matrix B min: {np.min(B_float)}, max: {np.max(B_float)}")
        
        game = pygambit.Game.from_arrays(A_float, B_float)
        
        # Add player labels
        game.players[0].label = "Alice"
        game.players[1].label = "Bob"
        
        # Find a Nash equilibrium using Gambit
        # Using LCP solver which is equivalent to Lemke-Howson
        results = pygambit.nash.lcp_solve(game, rational=True, stop_after = 3)
        
        with open(self.out_fname, 'w') as f:
            sys.stdout = f
            for eq in results.equilibria:
                alice_strat = eq['Alice']
                alice_probs = [float(p) for _, p in alice_strat]
                
                bob_strat = eq['Bob']
                bob_probs = [float(p) for _, p in bob_strat]
                
                self.print_results(alice_probs, 'Alice')
                self.print_results(bob_probs, 'Bob')
                print('-------------')

        sys.stdout = sys.__stdout__  

        return

    def get_payoff_element(self, alice_strat: list, bob_strat: list, bob: bool = False) -> np.float64:
        payoff = np.float64(0)
        for play in range(1, self.num_plays + 1):
            prefactor = self.get_prefactor(play, alice_strat, bob_strat, bob)
            # Skip calculation if prefactor is zero
            if prefactor == 0:
                continue
            element = np.float64(prefactor * self.get_case(alice_strat, bob_strat, play, prefactor, bob))
            # Only add valid values
            if not np.isnan(element) and not np.isinf(element):
                payoff += element
        return payoff

    def test_quadratic_grid(self) -> None:
        print("Grid points:")
        print(self.grid)
        
        differences = np.diff(self.grid)
        print("\nDifferences between consecutive points:")
        print(differences)
        
        if all(differences[i] <= differences[i+1] for i in range(len(differences)-1)):
            print("\nVerification FAILED: Grid spacing is not decreasing toward max_K")
        else:
            print("\nVerification PASSED: Grid spacing is generally decreasing toward max_K")
        
        plt.figure(figsize=(10, 6))
        plt.plot(range(len(self.grid)), self.grid, 'o-')
        plt.title(f"Quadratic Grid Distribution (clustering_factor={self.clustering_factor})")
        plt.xlabel("Grid Index")
        plt.ylabel("Grover Iterations")
        plt.grid(True)
        plt.savefig("quadratic_grid_distribution.png")
        print("\nGrid distribution plot saved as 'quadratic_grid_distribution.png'")


def main():
    K = 25 #number of pure strategies
    num_plays = 2 #number of plays
    #D = 82047028459932.62
    #D = 119116256505723.5 #difficulty as of May 9 2025
    D = 3651011.631 #difficulty as of Feb 26 2013
    clustering_factor = 2.0
    gamma = 0.5
    beta = 1.0  # fraction of max_K that can be applied in block mining window
    
    payoff_builder = BuildPayoff(K, num_plays, D, clustering_factor, gamma, beta, scale_with_D=True)
    
    #payoff_builder.test_quadratic_grid()
    
    print("Building payoff matrices...")
    A = payoff_builder.get_payoff()
    B = payoff_builder.get_payoff(bob=True)

    print(A, B)

    print("Payoff matrices created!")
    
    payoff_builder.get_nash_eq_pygambit(A, B)

if __name__ == '__main__':
    main()