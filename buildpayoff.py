import numpy as np
import math
import sys
import pygambit
from util import cartesian
from functools import lru_cache
import matplotlib.pyplot as plt

class BuildPayoff:
    def __init__(self, K: int, num_plays: int, D: float, clustering_factor: float = 1.0, gamma: float = 0.5, out_fname = 'output.txt', scale_with_D: bool = False, stop_after: int = 1):
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
        S = cartesian(arrs)
        
        valid_indices = []
        for idx, strat in enumerate(S):
            total_iterations = sum(self.grid_to_iterations(s) for s in strat)
            if total_iterations <= self.max_K:
                valid_indices.append(idx)
        
        S_valid = S[valid_indices]
        dim = len(S_valid)
        
        print(f"Filtered strategy set size: {dim} (out of {len(S)} total)")

        if not bob:
            max_K_index = self.K
            expected_strategies = []
            for i in range(self.num_plays):
                strat = [0] * self.num_plays
                strat[i] = max_K_index
                expected_strategies.append(tuple(strat))
            
            print(f"\nChecking for expected boundary strategies:")
            all_found = True
            for expected in expected_strategies:
                found = any(tuple(s) == expected for s in S_valid)
                iterations = [self.grid_to_iterations(idx) for idx in expected]
                status = 'FOUND' if found else 'NOT FOUND'
                print(f"  Strategy {expected} (iterations: {iterations}): {status}")
                if not found:
                    all_found = False
            
            if all_found:
                print("All expected boundary strategies are present in filtered set")
            else:
                print("Some expected boundary strategies are MISSING from filtered set")




        A = np.zeros((dim, dim), dtype=np.float64)

        original_gamma = self.gamma
        if bob:
            self.gamma = 1 - self.gamma

        for row in range(dim):
            for col in range(dim):
                if bob:
                    alice_strat = S_valid[col]
                    bob_strat = S_valid[row]
                else:
                    alice_strat = S_valid[row]
                    bob_strat = S_valid[col]

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

        if row_cum < col_first_strat:
            return np.float64(1.0)
        
        col_cumulative = [self.get_cumulative_iterations(col_strat, i + 1) for i in range(len(col_strat))]

        num_col_strats = 0

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
        
        col_cumulative = [self.get_cumulative_iterations(col_strat, i + 1) for i in range(len(col_strat))]
        
        ell = 0  
        bob_last_cum = 0  
        
        for j, col_cum in enumerate(col_cumulative):
            if col_cum < row_cum:
                ell = j + 1
                bob_last_cum = col_cum
            else:
                break
        
        product_term = np.float64(1.0)
        
        for k in range(play - 1):  
            alice_cum_k = self.get_cumulative_iterations(row_strat, k + 1) 
            if alice_cum_k > bob_last_cum:
                alice_iterations_k = self.grid_to_iterations(row_strat[k])
                product_term *= (1 - self.p(alice_iterations_k, self.D))
        
        bob_aqms_iterations = row_cum - bob_last_cum
        
        aqms_term = (self.p(current_row_iterations, self.D) * 
                    product_term * 
                    self.p(bob_aqms_iterations, self.D))
        
        return np.float64(aqms_term)

    def print_results(self, result: list, player: str) -> None:
        set_K = np.arange(0, self.K + 1)
        cart_prod = cartesian((set_K for x in range(self.num_plays)))
        
        valid_indices = []
        for idx, strat in enumerate(cart_prod):
            total_iterations = sum(self.grid_to_iterations(s) for s in strat)
            if total_iterations <= self.max_K:
                valid_indices.append(idx)
        
        cart_prod_valid = cart_prod[valid_indices]
        
        for i, value in enumerate(result):
            if abs(value) != 0.0:
                strat = [self.grid_to_iterations(x) for x in cart_prod_valid[i]]
                print('{} {} {}'.format(player, strat, value))
        return 

    def analyze_extreme_payoffs(self, A: np.ndarray, B: np.ndarray, player_name: str = "Alice") -> None:
        matrix = A if player_name == "Alice" else B
        
        set_K = np.arange(0, self.K + 1)
        cart_prod = cartesian((set_K for x in range(self.num_plays)))
        
        valid_indices = []
        for idx, strat in enumerate(cart_prod):
            total_iterations = sum(self.grid_to_iterations(s) for s in strat)
            if total_iterations <= self.max_K:
                valid_indices.append(idx)
        
        cart_prod_valid = cart_prod[valid_indices]
        
        max_val = np.max(matrix)
        min_val = np.min(matrix)
        
        print(f"\n=== EXTREME PAYOFF ANALYSIS FOR {player_name.upper()} ===")
        print(f"Maximum payoff: {max_val}")
        print(f"Minimum payoff: {min_val}")
        
        max_positions = np.where(matrix == max_val)
        max_row_col_pairs = list(zip(max_positions[0], max_positions[1]))
        
        min_positions = np.where(matrix == min_val)
        min_row_col_pairs = list(zip(min_positions[0], min_positions[1]))
        
        print(f"\nMAXIMUM PAYOFF COMBINATIONS (Value: {max_val}):")
        print(f"Found {len(max_row_col_pairs)} combination(s)")
        
        for i, (row_idx, col_idx) in enumerate(max_row_col_pairs):
            row_strat_indices = cart_prod_valid[row_idx]
            col_strat_indices = cart_prod_valid[col_idx]
            
            row_strat_iterations = [self.grid_to_iterations(x) for x in row_strat_indices]
            col_strat_iterations = [self.grid_to_iterations(x) for x in col_strat_indices]
            
            print(f"  {i+1}. Row strategy (indices): {list(row_strat_indices)} -> Iterations: {row_strat_iterations}")
            print(f"     Col strategy (indices): {list(col_strat_indices)} -> Iterations: {col_strat_iterations}")
        
        print(f"\nMINIMUM PAYOFF COMBINATIONS (Value: {min_val}):")
        print(f"Found {len(min_row_col_pairs)} combination(s)")
        
        for i, (row_idx, col_idx) in enumerate(min_row_col_pairs):
            row_strat_indices = cart_prod_valid[row_idx]
            col_strat_indices = cart_prod_valid[col_idx]
            
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
        plt.savefig("images/quadratic_grid_distribution.png")
        print("\nGrid distribution plot saved as 'quadratic_grid_distribution.png'")


    def compute_expected_payoff(self, alice_mixed_strat: dict, bob_mixed_strat: dict, player: str = "Alice") -> np.float64:
        expected_payoff = np.float64(0.0)
        
        original_gamma = self.gamma
        
        if player == "Bob":
            self.gamma = 1 - self.gamma
        
        for alice_strat, alice_prob in alice_mixed_strat.items():
            for bob_strat, bob_prob in bob_mixed_strat.items():
                alice_strat_list = list(alice_strat)
                bob_strat_list = list(bob_strat)
                
                if player == "Alice":
                    payoff = self.get_payoff_element(alice_strat_list, bob_strat_list)
                else:  # Bob
                    payoff = self.get_payoff_element(bob_strat_list, alice_strat_list)
                
                expected_payoff += alice_prob * bob_prob * payoff
        
        self.gamma = original_gamma
        
        return expected_payoff

def main():
    K =  100 #number of pure strategies (including 0 so K=1 means 2 strategies)
    num_plays = 1 #number of plays
    #D = 82047028459932.62
    D = 119116256505723.5 #difficulty as of May 9 2025
    #D = 3651011.631 #difficulty as of Feb 26 2013
    clustering_factor = 2.0
    gamma = 0.5

    builder = BuildPayoff(K, num_plays, D, clustering_factor, gamma, scale_with_D = False, stop_after = 1)
    builder.test_quadratic_grid()
    A = builder.get_payoff()
    B = builder.get_payoff(bob=True)
    print("Payoff matrix for Alice:")
    print(A)
    print("Payoff matrix for Bob:")
    print(B)

    print('Payoff matrices created!')
    
    builder.get_nash_eq_pygambit(A, B)


if __name__ == "__main__":
    main()