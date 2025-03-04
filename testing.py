import numpy as np
import math

# Example values (replace with your actual values)
difficulty = 82047028459932.62
classical_block_rate = 1/600


def time_to_iterations(time: float, difficulty: float) -> int:
    optimal_iterations = np.floor(np.pi / 4 * np.sqrt(difficulty))
    time_per_iteration = 600 / optimal_iterations  # Assumes 600s block time for classical
    return int(time // time_per_iteration)

def iterations_to_time(iterations: int, difficulty: float) -> float:
    optimal_iterations = np.floor(np.pi / 4 * np.sqrt(difficulty))
    time_per_iteration = 600 / optimal_iterations
    return iterations * time_per_iteration

# Test Cases
test_times = [0.1, 1, 60, 600, 3600, 86400]  # Seconds
print(f"Difficulty: {difficulty}")
print(f"Classical Block Rate: {classical_block_rate}")
print("\n--- Time to Iterations ---")
for time in test_times:
    iterations = time_to_iterations(time, difficulty)
    print(f"Time: {time:.2f}s, Iterations: {iterations}")

print("\n--- Iterations to Time & Back to Iterations (Consistency Check) ---")
test_iterations = [1, 10, 100, 1000, 10000, 100000]
for n in test_iterations:
    time = iterations_to_time(n, difficulty)
    iterations_back = time_to_iterations(time, difficulty)
    print(f"Original Iterations: {n}, Time: {time:.2f}s, Iterations Back: {iterations_back}")

# Print optimal iterations value
optimal_iterations = np.floor(np.pi / 4 * np.sqrt(difficulty))
print(f'\nOptimal iterations: {optimal_iterations}')