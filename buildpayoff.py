import numpy as np
import math
import sys
import pygambit
from util import cartesian
from typing import Callable
from functools import lru_cache
import matplotlib.pyplot as plt

class BuildPayoff:
    def __init__(self, K: int, num_plays: int, D: float, clustering_factor: float = 1.0, gamma: float = 0.5, beta: float = 1.0, out_fname = 'output.txt', scale_with_D: bool = False, stop_after: int = 1):
        self.K = K
        self.num_plays = num_plays
        self.D = D
        self.scale_with_D = scale_with_D
        self.stop_after = stop_after

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

    def create_quadratic_grid(self) -> np.ndarray:
        linear_grid = np.linspace(0, 1, self.K + 1)
        quadratic_grid = 1 - (1 - linear_grid)**self.clustering_factor
        scaled_grid = quadratic_grid * self.max_K 
        return np.round(scaled_grid).astype(int)

    def grid_to_iterations(self, grid_point: int) -> int:
        return self.grid[grid_point]

    @staticmethod
    @lru_cache(maxsize=None)
    def p(k: int, D: float) -> np.float64:
        return np.float64((math.sin(2 * (k + 1/2) * math.asin(1/np.sqrt(D))))**2)

    def get_payoff(self, bob: bool = False) -> np.ndarray:
        set_K = np.arange(0, self.K + 1)
        arrs = (set_K for i in range(self.num_plays))
        S = cartesian(arrs) #cartesian product of the indices of the strategies

        dim = int(len(set_K) ** self.num_plays)

        A = np.zeros((dim, dim), dtype=np.float64)

        original_gamma = self.gamma
        if bob:
            self.gamma = 1 - self.gamma

        for row in range(dim):
            for col in range(dim):
                if bob:
                    alice_strat = S[col]
                    bob_strat = S[row]
                else:
                    alice_strat = S[row]
                    bob_strat = S[col]

                total_payoff = np.float64(0.0)
                for play in range(1, self.num_plays + 1):
                    total_payoff += self.calculate_payoff_for_play(alice_strat, bob_strat, play)

                A[row][col] = total_payoff
        
        self.gamma = original_gamma

        return np.nan_to_num(A, nan = 0.0, posinf = 0.0, neginf = 0.0)
    
    def calculate_payoff_for_play(self, row_strat: list[int], col_strat: list[int], play: int) -> np.float64:
        prefactor = self.get_prefactor(row_strat, play)
        
        if prefactor == 0:
            return np.float64(0.0)
        
        row_cum = self.get_cumulative_iterations(row_strat, play)

        max_allowed_iterations = self.beta * self.max_K
        if row_cum > max_allowed_iterations:
            return np.float64(0.0)
        
        success_part = self.get_success_failure_part(row_strat, col_strat, play, row_cum)
        aggressive_part = self.get_aggressive_part(row_strat, col_strat, play, row_cum)

        total_payoff = prefactor * success_part + self.gamma * aggressive_part

        return np.float64(total_payoff)

    def get_prefactor(self, strategy: list[int], play: int) -> np.float64:
        current_iterations = self.grid_to_iterations(strategy[play - 1])
        prefactor = self.p(current_iterations, self.D)

        for prev_play in range(play - 1):
            prev_iterations = self.grid_to_iterations(strategy[prev_play])
            prefactor *= (1 - self.p(prev_iterations, self.D))

        return np.float64(prefactor)
    
    def get_cumulative_iterations(self, strategy: list[int], up_to_play: int) -> int:
        return sum(self.grid_to_iterations(strategy[i]) for i in range(up_to_play))

    def get_success_failure_part(self, row_strat: list[int], col_strat: list[int], play: int, row_cum: int) -> np.float64:
        col_first_strat = self.grid_to_iterations(col_strat[0])

        # if row cumulative iterations are less than the first column strategy, return 1.0
        if row_cum < col_first_strat:
            return np.float64(1.0)
        
        # find which interval row player's cumulative iterations fall into
        col_cumulative = [self.get_cumulative_iterations(col_strat, i + 1) for i in range(len(col_strat))]

        num_col_strats = 0 #number of column strategies to include in product
        #find the case and then multiply by (1 - col_strat[i]) up to the num_col_strats

        for i, col_cum in enumerate(col_cumulative):
            if row_cum < col_cum:
                break
            elif row_cum == col_cum:
                num_col_strats = i + 1
                break
            else:
                num_col_strats = i + 1

        product = np.float64(1.0)
        for i in range(num_col_strats):
            col_iterations = self.grid_to_iterations(col_strat[i])
            product = product * (1 - self.p(col_iterations, self.D))

        return product
    
    def get_aggressive_part(self, row_strat: list[int], col_strat: list[int], play: int, row_cum: int) -> np.float64:
        current_row_iterations = self.grid_to_iterations(row_strat[play - 1])
        
        # find Bob's most recent measurement before Alice's current cumulative iterations
        col_cumulative = [self.get_cumulative_iterations(col_strat, i + 1) for i in range(len(col_strat))]
        
        # find the index ell of Bob's most recent measurement before row_cum
        ell = 0  
        bob_last_cum = 0  
        
        for j, col_cum in enumerate(col_cumulative):
            if col_cum < row_cum:
                ell = j + 1  # j+1 because col_cumulative is 0-indexed but we want 1-indexed
                bob_last_cum = col_cum
            else:
                break
        
        # calculate product 
        product_term = np.float64(1.0)
        
        for k in range(play - 1):  
            alice_cum_k = self.get_cumulative_iterations(row_strat, k + 1) 
            if alice_cum_k > bob_last_cum:
                alice_iterations_k = self.grid_to_iterations(row_strat[k])
                product_term *= (1 - self.p(alice_iterations_k, self.D))
        
        # calculate Bob's AQMS iterations: A_i - B_ell
        bob_aqms_iterations = row_cum - bob_last_cum
        
        aqms_term = (self.p(current_row_iterations, self.D) * 
                    product_term * 
                    self.p(bob_aqms_iterations, self.D))
        
        return np.float64(aqms_term)

    def print_results(self, result: list, player: str) -> None:
        set_K = np.arange(0, self.K + 1)
        cart_prod = cartesian((set_K for x in range(self.num_plays)))
        for i, value in enumerate(result):
            if abs(value) != 0.0:
                strat = [self.grid_to_iterations(x) for x in cart_prod[i]]
                print('{} {} {}'.format(player, strat, value))
        return 

    def analyze_extreme_payoffs(self, A: np.ndarray, B: np.ndarray, player_name: str = "Alice") -> None:
        """
        Find and print the grid combinations that result in highest and lowest payoffs.
        Handles ties by printing all combinations that achieve the extreme values.
        """
        matrix = A if player_name == "Alice" else B
        
        # Get the cartesian product of strategies
        set_K = np.arange(0, self.K + 1)
        cart_prod = cartesian((set_K for x in range(self.num_plays)))
        
        # Find max and min values
        max_val = np.max(matrix)
        min_val = np.min(matrix)
        
        print(f"\n=== EXTREME PAYOFF ANALYSIS FOR {player_name.upper()} ===")
        print(f"Maximum payoff: {max_val}")
        print(f"Minimum payoff: {min_val}")
        
        # Find all positions with max values
        max_positions = np.where(matrix == max_val)
        max_row_col_pairs = list(zip(max_positions[0], max_positions[1]))
        
        # Find all positions with min values  
        min_positions = np.where(matrix == min_val)
        min_row_col_pairs = list(zip(min_positions[0], min_positions[1]))
        
        print(f"\nMAXIMUM PAYOFF COMBINATIONS (Value: {max_val}):")
        print(f"Found {len(max_row_col_pairs)} combination(s)")
        
        for i, (row_idx, col_idx) in enumerate(max_row_col_pairs):
            row_strat_indices = cart_prod[row_idx]
            col_strat_indices = cart_prod[col_idx]
            
            row_strat_iterations = [self.grid_to_iterations(x) for x in row_strat_indices]
            col_strat_iterations = [self.grid_to_iterations(x) for x in col_strat_indices]
            
            print(f"  {i+1}. Row strategy (indices): {list(row_strat_indices)} -> Iterations: {row_strat_iterations}")
            print(f"     Col strategy (indices): {list(col_strat_indices)} -> Iterations: {col_strat_iterations}")
        
        print(f"\nMINIMUM PAYOFF COMBINATIONS (Value: {min_val}):")
        print(f"Found {len(min_row_col_pairs)} combination(s)")
        
        for i, (row_idx, col_idx) in enumerate(min_row_col_pairs):
            row_strat_indices = cart_prod[row_idx]
            col_strat_indices = cart_prod[col_idx]
            
            row_strat_iterations = [self.grid_to_iterations(x) for x in row_strat_indices]
            col_strat_iterations = [self.grid_to_iterations(x) for x in col_strat_indices]
            
            print(f"  {i+1}. Row strategy (indices): {list(row_strat_indices)} -> Iterations: {row_strat_iterations}")
            print(f"     Col strategy (indices): {list(col_strat_indices)} -> Iterations: {col_strat_iterations}")

    def get_nash_eq_pygambit(self, A: np.ndarray, B: np.ndarray) -> None:
        A_float = np.nan_to_num(A, nan=0.0, posinf=0.0, neginf=0.0)
        B_float = np.nan_to_num(B, nan=0.0, posinf=0.0, neginf=0.0)
        
        if np.any(np.isnan(A_float)) or np.any(np.isinf(A_float)) or np.any(np.isnan(B_float)) or np.any(np.isinf(B_float)):
            print("Warning: Matrices still contain invalid values after cleaning.")
            
        print(f"Matrix A min: {np.min(A_float)}, max: {np.max(A_float)}")
        print(f"Matrix B min: {np.min(B_float)}, max: {np.max(B_float)}")
        
        game = pygambit.Game.from_arrays(A_float, B_float)
        
        game.players[0].label = "Alice"
        game.players[1].label = "Bob"
        
        # Find a Nash equilibrium using Gambit
        # Using LCP solver which is equivalent to Lemke-Howson
        results = pygambit.nash.lcp_solve(game, rational=True, stop_after=self.stop_after)

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

    def get_payoff_element(self, row_strat: list, col_strat: list) -> np.float64:
        total_payoff = np.float64(0.0)
        for play in range(1, self.num_plays + 1):
            total_payoff += self.calculate_payoff_for_play(row_strat, col_strat, play)
        return np.float64(total_payoff)

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
    K = 10 #number of pure strategies (including 0 so K=1 means 2 strategies)
    num_plays = 3 #number of plays
    #D = 82047028459932.62
    #D = 119116256505723.5 #difficulty as of May 9 2025
    D = 3651011.631 #difficulty as of Feb 26 2013
    clustering_factor = 2.0
    gamma = 0.5
    beta = 3.0  # fraction of max_K that can be applied in block mining window

    builder = BuildPayoff(K, num_plays, D, clustering_factor, gamma, beta, scale_with_D = True, stop_after = 2)
    builder.test_quadratic_grid()
    A = builder.get_payoff()
    B = builder.get_payoff(bob=True)
    print("Payoff matrix for Alice:")
    print(A)
    print("Payoff matrix for Bob:")
    print(B)

    print('Payoff matrices created!')
    
    #builder.analyze_extreme_payoffs(A, B, "Alice")
    
    builder.get_nash_eq_pygambit(A, B)


if __name__ == "__main__":
    main()