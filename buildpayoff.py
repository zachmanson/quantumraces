import numpy as np
import math
import sys
import pygambit
from util import cartesian
from functools import lru_cache
import matplotlib.pyplot as plt
from multiprocessing import Pool
import os

_builder_worker = None

def _init_builder_worker(builder):
    global _builder_worker
    _builder_worker = builder

def _compute_payoff_row(args):
    row, bob = args
    builder = _builder_worker
    S_valid = builder.S_valid
    dim = len(S_valid)
    row_vals = np.zeros(dim, dtype=np.float64)
    for col in range(dim):
        if bob:
            alice_strat = S_valid[col]
            bob_strat = S_valid[row]
        else:
            alice_strat = S_valid[row]
            bob_strat = S_valid[col]
        total_payoff = np.float64(0.0)
        for play in range(1, builder.num_plays + 1):
            total_payoff += builder.calculate_payoff_for_play(alice_strat, bob_strat, play)
        row_vals[col] = total_payoff
    return row_vals


class BuildPayoff:
    def __init__(self, n_q: int, num_plays: int, D: float, clustering_factor: float = 1.0, gamma: float = 0.5, out_fname = 'output.txt', scale_with_D: bool = False, stop_after: int = 1):
        self.n_q = n_q
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
        linear_grid = np.linspace(0, 1, self.n_q)
        quadratic_grid = 1 - (1 - linear_grid)**self.clustering_factor
        scaled_grid = quadratic_grid * self.max_K
        rounded_grid = np.round(scaled_grid).astype(int)

        unique_grid = np.unique(rounded_grid)
        num_removed = len(rounded_grid) - len(unique_grid)

        print(f"Grid points before deduplication: {len(rounded_grid)}")
        print(f"Grid points after deduplication:  {len(unique_grid)} ({num_removed} duplicate(s) removed)")

        # Update n_q to reflect the actual number of unique strategies (0-indexed)
        self.n_q = len(unique_grid) - 1

        return unique_grid

    def grid_to_iterations(self, grid_point: int) -> int:
        return self.grid[grid_point]

    @staticmethod
    @lru_cache(maxsize=None)
    def p(k: int, D: float) -> np.float64:
        return np.float64((math.sin(2 * (k + 1/2) * math.asin(1/np.sqrt(D))))**2)

    def get_payoff(self, bob: bool = False) -> np.ndarray:
        set_K = np.arange(0, self.n_q + 1)
        arrs = (set_K for i in range(self.num_plays))
        S = cartesian(arrs)
        
        S_valid = S[np.sum(self.grid[S], axis=1) <= self.max_K]
        self.S_valid = S_valid
        dim = len(S_valid)

        print(f"Filtered strategy set size: {dim} (out of {len(S)} total)")

        if not bob:
            max_K_index = self.n_q
            expected_strategies = []
            for i in range(self.num_plays):
                strat = [0] * self.num_plays
                strat[i] = max_K_index
                expected_strategies.append(tuple(strat))
            
            print(f"\nChecking boundary pure strategies:")
            all_found = True
            for expected in expected_strategies:
                found = any(tuple(s) == expected for s in S_valid)
                iterations = [self.grid_to_iterations(idx) for idx in expected]
                status = 'FOUND' if found else 'NOT FOUND'
                print(f"  Strategy {expected} (iterations: {iterations}): {status}")
                if not found:
                    all_found = False
            
            if all_found:
                print("All expected boundary pure strategies found in filtered set")
            else:
                print("Some expected boundary pure strategies NOT found in filtered set")

        original_gamma = self.gamma
        if bob:
            self.gamma = 1 - self.gamma

        n_workers = min(os.cpu_count() or 1, dim)
        with Pool(processes=n_workers, initializer=_init_builder_worker, initargs=(self,)) as pool:
            rows = pool.map(_compute_payoff_row, [(row, bob) for row in range(dim)])
        A = np.array(rows, dtype=np.float64)
        
        self.gamma = original_gamma

        return np.nan_to_num(A, nan = 0.0, posinf = 0.0, neginf = 0.0)
    
    def calculate_payoff_for_play(self, row_strat: list[int], col_strat: list[int], play: int) -> np.float64:
        prefactor = self.get_prefactor(row_strat, play)

        if prefactor == 0:
            return np.float64(0.0)

        row_cum = self.get_cumulative_iterations(row_strat, play)
        col_cumulative = [self.get_cumulative_iterations(col_strat, i + 1) for i in range(len(col_strat))]

        success_part = self.get_success_failure_part(row_cum, col_cumulative)
        aggressive_part = self.get_aggressive_part(row_strat, play, row_cum, col_cumulative)

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

    def get_success_failure_part(self, row_cum: int, col_cumulative: list[int]) -> np.float64:
        if row_cum < col_cumulative[0]:
            return np.float64(1.0)

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
            col_iterations = col_cumulative[i] - (col_cumulative[i - 1] if i > 0 else 0)
            product = product * (1 - self.p(col_iterations, self.D))

        return product
    
    def get_aggressive_part(self, row_strat: list[int], play: int, row_cum: int, col_cumulative: list[int]) -> np.float64:
        current_row_iterations = self.grid_to_iterations(row_strat[play - 1])

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

    def print_results(self, result: list, player: str, file=None) -> None:
        for i, value in enumerate(result):
            if abs(value) != 0.0:
                strat = [self.grid_to_iterations(x) for x in self.S_valid[i]]
                print('{} {} {}'.format(player, strat, value), file=file)
        return

    def analyze_extreme_payoffs(self, A: np.ndarray, B: np.ndarray, player_name: str = "Alice") -> None:
        matrix = A if player_name == "Alice" else B

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
            row_strat_indices = self.S_valid[row_idx]
            col_strat_indices = self.S_valid[col_idx]

            row_strat_iterations = [self.grid_to_iterations(x) for x in row_strat_indices]
            col_strat_iterations = [self.grid_to_iterations(x) for x in col_strat_indices]

            print(f"  {i+1}. Row strategy (indices): {list(row_strat_indices)} -> Iterations: {row_strat_iterations}")
            print(f"     Col strategy (indices): {list(col_strat_indices)} -> Iterations: {col_strat_iterations}")

        print(f"\nMINIMUM PAYOFF COMBINATIONS (Value: {min_val}):")
        print(f"Found {len(min_row_col_pairs)} combination(s)")

        for i, (row_idx, col_idx) in enumerate(min_row_col_pairs):
            row_strat_indices = self.S_valid[row_idx]
            col_strat_indices = self.S_valid[col_idx]

            row_strat_iterations = [self.grid_to_iterations(x) for x in row_strat_indices]
            col_strat_iterations = [self.grid_to_iterations(x) for x in col_strat_indices]

            print(f"  {i+1}. Row strategy (indices): {list(row_strat_indices)} -> Iterations: {row_strat_iterations}")
            print(f"     Col strategy (indices): {list(col_strat_indices)} -> Iterations: {col_strat_iterations}")

    def get_nash_eq_pygambit(self, A: np.ndarray, B: np.ndarray) -> None:
        A_float = np.nan_to_num(A, nan=0.0, posinf=0.0, neginf=0.0)
        B_float = np.nan_to_num(B, nan=0.0, posinf=0.0, neginf=0.0)

        print(f"Matrix A min: {np.min(A_float)}, max: {np.max(A_float)}")
        print(f"Matrix B min: {np.min(B_float)}, max: {np.max(B_float)}")

        game = pygambit.Game.from_arrays(A_float, B_float)

        game.players[0].label = "Alice"
        game.players[1].label = "Bob"

        results = pygambit.nash.lcp_solve(game, rational=True, stop_after=self.stop_after)

        with open(self.out_fname, 'w') as f:
            for eq in results.equilibria:
                alice_strat = eq['Alice']
                alice_probs = [float(p) for _, p in alice_strat]

                bob_strat = eq['Bob']
                bob_probs = [float(p) for _, p in bob_strat]

                self.print_results(alice_probs, 'Alice', file=f)
                self.print_results(bob_probs, 'Bob', file=f)
                print('-------------', file=f)

        return
    

    def eliminate_dominated(self, A, B):
        """Iteratively eliminate strictly dominated strategies.
        Also updates self.S_valid to reflect the surviving strategies."""
        row_indices = np.arange(A.shape[0])
        col_indices = np.arange(A.shape[1])
        changed = True
        while changed:
            changed = False
            # Check row player (rows of A)
            # dominated_rows[i] = True if any row j beats row i in every column
            dominated_rows = np.any(np.all(A[:, np.newaxis, :] > A[np.newaxis, :, :], axis=2), axis=0)
            keep_rows = np.where(~dominated_rows)[0]
            if len(keep_rows) < A.shape[0]:
                A, B = A[keep_rows], B[keep_rows]
                row_indices = row_indices[keep_rows]
                changed = True

            # Check column player (columns of B)
            # dominated_cols[j] = True if any column j' beats column j in every row
            dominated_cols = np.any(np.all(B[:, :, np.newaxis] > B[:, np.newaxis, :], axis=0), axis=0)
            keep_cols = np.where(~dominated_cols)[0]
            if len(keep_cols) < A.shape[1]:
                A, B = A[:, keep_cols], B[:, keep_cols]
                col_indices = col_indices[keep_cols]
                changed = True

        self.S_valid = self.S_valid[row_indices]
        return A, B

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
            print("\nGrid spacing is NOT decreasing toward upper bound!")
        else:
            print("\nGrid spacing is generally decreasing toward upper bound!")
        
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

