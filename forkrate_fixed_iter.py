import numpy as np
import random
import math
import matplotlib.pyplot as plt
from multiprocessing import Pool, cpu_count
import time

class EfficientQuantumMiningSimulator:
    def __init__(self,
                 num_simulations: int = 1000,
                 classical_block_rate: float = 1/600, # blocks per second: 1 every 10 minutes
                 quantum_simulation_time: float = 86400.0, # seconds in a day
                 difficulty: float = 119116256505723.5, # current difficulty
                 fixed_iterations: int = 51471, # fixed Grover iterations
                 epsilon: float = 1.0 # fraction of optimal iterations affecting speed
                ) -> None:
        self.num_simulations = num_simulations
        self.classical_block_rate = classical_block_rate
        self.quantum_simulation_time = quantum_simulation_time
        self.difficulty = difficulty
        self.fixed_iterations = fixed_iterations
        self.epsilon = epsilon
        
        # Calculate time per iteration based on epsilon
        self.seconds_per_iteration = 600 / (fixed_iterations * epsilon)
        # Time for one complete set of iterations
        self.time_per_measurement = self.seconds_per_iteration * fixed_iterations
        
        # Pre-calculate the success probability for fixed iterations
        self.full_measurement_prob = self.measurement_probability(fixed_iterations)
        
    def measurement_probability(self, iterations: int) -> float:
        """Calculate probability of successful measurement after given iterations"""
        theta = math.asin(1 / math.sqrt(self.difficulty))
        probability = (math.sin((2 * iterations + 1) * theta))**2
        return probability
    
    def simulate_day(self):
        """Simulate a full day of quantum mining"""
        total_blocks = 0
        quantum_blocks = 0  # Blocks found by Alice or Bob
        total_forks = 0
        current_time = 0.0
        
        # Pre-generate all classical block times for efficiency
        classical_block_times = []
        next_classical_time = 0.0
        while next_classical_time < self.quantum_simulation_time:
            next_classical_time += np.random.exponential(1/self.classical_block_rate)
            if next_classical_time < self.quantum_simulation_time:
                classical_block_times.append(next_classical_time)
        
        # Index to track the next classical block
        classical_idx = 0
        
        # Start the simulation
        while current_time < self.quantum_simulation_time:
            # Time of next quantum measurement (both Alice and Bob measure at same time)
            next_quantum_time = current_time + self.time_per_measurement
            
            # Check if a classical block arrives before next quantum measurement
            if classical_idx < len(classical_block_times) and classical_block_times[classical_idx] < next_quantum_time:
                # Classical block arrived first
                classical_time = classical_block_times[classical_idx]
                classical_idx += 1
                
                # Count the classical block
                total_blocks += 1
                
                # Calculate how many iterations Alice and Bob completed before being interrupted
                completed_ratio = (classical_time - current_time) / self.time_per_measurement
                completed_iterations = int(self.fixed_iterations * completed_ratio)
                
                # Calculate probability based on partial iterations
                partial_prob = self.measurement_probability(completed_iterations)
                
                # Check if Alice finds a block
                if random.random() <= partial_prob:
                    total_blocks += 1
                    quantum_blocks += 1
                    total_forks += 1  # Fork occurs because classical network also found block
                
                # Check if Bob finds a block
                if random.random() <= partial_prob:
                    total_blocks += 1
                    quantum_blocks += 1
                    total_forks += 1  # Fork occurs because classical network also found block
                
                current_time = classical_time
            else:
                # Quantum measurement happens first
                current_time = next_quantum_time
                
                # Check if Alice finds a block
                alice_success = random.random() <= self.full_measurement_prob
                
                # Check if Bob finds a block
                bob_success = random.random() <= self.full_measurement_prob
                
                if alice_success:
                    total_blocks += 1
                    quantum_blocks += 1
                    
                if bob_success:
                    total_blocks += 1
                    quantum_blocks += 1
                    
                if alice_success and bob_success:
                    total_forks += 1  # fork occurs because both Alice and Bob found blocks
        
        fork_rate = total_forks / total_blocks if total_blocks > 0 else 0
        quantum_percentage = quantum_blocks / total_blocks * 100 if total_blocks > 0 else 0
        
        return fork_rate, total_blocks, total_forks, quantum_percentage
    
    def simulate_all(self):
        total_fork_rate = 0.0
        total_blocks = 0.0
        total_forks = 0.0
        total_quantum_percentage = 0.0
        
        start_time = time.time()
        
        for i in range(self.num_simulations):
            if i > 0 and i % 100 == 0:
                elapsed = time.time() - start_time
                remaining = elapsed * (self.num_simulations - i) / i
                print(f"Completed {i}/{self.num_simulations} simulations. Estimated time remaining: {remaining:.2f} seconds")
                
            fork_rate, blocks, forks, quantum_percentage = self.simulate_day()
            total_fork_rate += fork_rate
            total_blocks += blocks
            total_forks += forks
            total_quantum_percentage += quantum_percentage
        
        avg_fork_rate = total_fork_rate / self.num_simulations
        avg_blocks = total_blocks / self.num_simulations
        avg_forks = total_forks / self.num_simulations
        avg_quantum_percentage = total_quantum_percentage / self.num_simulations
        
        return avg_fork_rate, avg_blocks, avg_forks, avg_quantum_percentage

def worker_function(args):
    # worker function for parallel processing
    epsilon, num_simulations, params = args
    simulator = EfficientQuantumMiningSimulator(
        num_simulations=num_simulations,
        classical_block_rate=params.get('classical_block_rate', 1/600),
        quantum_simulation_time=params.get('quantum_simulation_time', 86400.0),
        difficulty=params.get('difficulty', 119116256505723.5),
        fixed_iterations=params.get('fixed_iterations', 51471),
        epsilon=epsilon
    )
    return epsilon, simulator.simulate_all()

def simulate_across_epsilons(epsilons, num_simulations=1000, parallel=True, **params):
    results = {}
    
    if parallel:
        # Use multiprocessing for parallel execution
        print(f"Starting parallel simulation with {cpu_count()} processes")
        args = [(epsilon, num_simulations, params) for epsilon in epsilons]
        
        with Pool(processes=cpu_count()) as pool:
            for epsilon, result in pool.map(worker_function, args):
                results[epsilon] = result
                print(f"epsilon = {epsilon}: Fork Rate = {result[0]:.6f}, Blocks = {result[1]:.2f}, "
                      f"Forks = {result[2]:.2f}, Quantum % = {result[3]:.2f}%")
    else:
        # Sequential execution
        for epsilon in epsilons:
            print(f"Simulating with epsilon = {epsilon}")
            simulator = EfficientQuantumMiningSimulator(
                num_simulations=num_simulations,
                classical_block_rate=params.get('classical_block_rate', 1/600),
                quantum_simulation_time=params.get('quantum_simulation_time', 86400.0),
                difficulty=params.get('difficulty', 119116256505723.5),
                fixed_iterations=params.get('fixed_iterations', 51471),
                epsilon=epsilon
            )
            result = simulator.simulate_all()
            results[epsilon] = result
            print(f"epsilon = {epsilon}: Fork Rate = {result[0]:.6f}, Blocks = {result[1]:.2f}, "
                  f"Forks = {result[2]:.2f}, Quantum % = {result[3]:.2f}%")
    
    # Prepare data for plotting
    sorted_epsilons = sorted(results.keys())
    fork_rates = [results[epsilon][0] for epsilon in sorted_epsilons]
    blocks_found = [results[epsilon][1] for epsilon in sorted_epsilons]
    forks_found = [results[epsilon][2] for epsilon in sorted_epsilons]
    quantum_percentages = [results[epsilon][3] for epsilon in sorted_epsilons]
    
    attack_threshold = [(1 - fork_rate)/(2 - fork_rate) for fork_rate in fork_rates]
    # Create plots
    plt.figure(figsize=(18, 10))

    plt.subplot(3, 2, 1)
    plt.plot(sorted_epsilons, fork_rates, 'o-', color='blue')
    plt.xscale('log')
    plt.xlabel('# of Grover executions in mining window $\\epsilon$')
    plt.ylabel('Average Fork Rate')
    plt.title('Network fork rate with fixed iterations')
    plt.grid(True)

    plt.subplot(3, 2, 2)
    plt.plot(sorted_epsilons, attack_threshold, 'o-', color='cyan')
    plt.xscale('log')
    plt.xlabel('# of Grover executions in mining window $\\epsilon$')
    plt.ylabel('51% Attack Threshold')
    plt.ylim(0.4, 0.6)
    plt.title('51% Attack Threshold with fixed iterations')
    plt.grid(True)

    plt.subplot(3, 2, 3)
    plt.plot(sorted_epsilons, blocks_found, 'o-', color='green')
    plt.xscale('log')
    plt.xlabel('# of Grover executions in mining window $\\epsilon$')
    plt.ylabel('Average Blocks Found Per Day')
    plt.title('Blocks per day with fixed iterations')
    plt.grid(True)

    plt.subplot(3, 2, 4)
    plt.plot(sorted_epsilons, forks_found, 'o-', color='red')
    plt.xscale('log')
    plt.xlabel('# of Grover executions in mining window $\\epsilon$')
    plt.ylabel('Average Forks Found Per Day')
    plt.title('Forks per day with fixed iterations')
    plt.grid(True)

    plt.subplot(3, 2, 5)
    plt.plot(sorted_epsilons, quantum_percentages, 'o-', color='purple')
    plt.xscale('log')
    plt.xlabel('# of Grover executions in mining window $\\epsilon$')
    plt.ylabel('Quantum Blocks (%)')
    plt.title('Percentage of blocks found by quantum miners')
    plt.grid(True)

    plt.tight_layout()
    plt.savefig('quantum_mining_results.png')
    
    return results

def main():
    epsilons = [0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 25.0, 50.0, 100.0, 250.0, 500.0, 1000.0, 2500.0, 5000.0, 10000.0, 25000.0, 50000.0, 100000.0, 250000.0, 500000.0, 1000000.0]
    
    results = simulate_across_epsilons(
        epsilons,
        num_simulations=1000,  
        parallel=True,         
        fixed_iterations=51471,
        quantum_simulation_time=86400.0,  # one day in seconds
        difficulty=119116256505723.5      
    )
    
    print("\nSummary Results:")
    print("-" * 80)
    print(f"{'epsilon':>10} | {'Fork Rate':>12} | {'Blocks/Day':>12} | {'Forks/Day':>12} | {'Quantum %':>12}")
    print("-" * 80)
    
    for epsilon in sorted(results.keys()):
        fork_rate, blocks, forks, quantum_pct = results[epsilon]
        print(f"{epsilon:10.2f} | {fork_rate:12.6f} | {blocks:12.2f} | {forks:12.2f} | {quantum_pct:12.2f}%")

if __name__ == '__main__':
    main()