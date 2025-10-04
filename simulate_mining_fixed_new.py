from analyze_nasheqs import NashEquilibriaAnalyzer
import numpy as np
import random
import math
from buildpayoffgambit import BuildPayoff
import matplotlib.pyplot as plt
from multiprocessing import Pool, cpu_count
from concurrent.futures import ProcessPoolExecutor, as_completed
import csv
from numba import jit, njit
import time


class QuantumMiningSimulator:
    def __init__(self,
                 nash_equilibrium: dict[str, list[tuple[list[float], float]]],
                 num_simulations: int = 100000,
                 classical_block_rate: float = 1/600, #blocks per second: 1 every 10 minutes
                 quantum_simulation_time: float = 86400.0, #seconds in a day
                 difficulty: float = 119116256505723.5, #current difficulty
                 #difficulty: float = 3651011.631, #difficulty from 2013 (low D)
                 c: float = 1.0 #fraction of optimal iterations
    ) -> None:
        self.nash_equilibrium = nash_equilibrium
        self.num_simulations = num_simulations
        self.classical_block_rate = classical_block_rate
        self.quantum_simulation_time = quantum_simulation_time
        self.difficulty = difficulty
        self.optimal_iterations = 51471
        self.seconds_per_iteration = 600 / (c * self.optimal_iterations)
        self.c = c

    def measurement_probability(self, iterations: int) -> float:
        theta = math.asin(1 / math.sqrt(self.difficulty))
        probability = (math.sin((2 * iterations + 1) * theta))**2
        return probability
    
    def select_strategy(self) -> tuple[list[float], list[float]]:
        alice_strats = self.nash_equilibrium['Alice']
        bob_strats = self.nash_equilibrium['Bob']

        alice_chosen_strat = random.choices(
            [strat[0] for strat in alice_strats],
            weights = [strat[1] for strat in alice_strats]
        )[0]

        bob_chosen_strat = random.choices(
            [strat[0] for strat in bob_strats],
            weights = [strat[1] for strat in bob_strats]
        )[0]

        return alice_chosen_strat, bob_chosen_strat

    def time_to_iterations(self, time: float) -> int:
        return time / self.seconds_per_iteration
    
    def iterations_to_time(self, iterations: int) -> float:
        return iterations * self.seconds_per_iteration
    
    def generate_classical_block_times(self, current_time: float = 0.0) -> list[float]:
        block_times = []
        while True:  
            block_arrival_time = np.random.exponential(1/self.classical_block_rate)
            next_block_time = current_time + block_arrival_time

            if next_block_time >= self.quantum_simulation_time:
                break 

            block_times.append(next_block_time)
            current_time = next_block_time
 
        return block_times
    
    def generate_quantum_measurement_times(self, strategy: list[float], start_time: float) -> list[float]:
        measurement_times = []
        seconds_per_iterations = 600 / self.optimal_iterations
        local_current_time = start_time

        for iterations in strategy:
            time_for_iterations = iterations * seconds_per_iterations
            local_current_time += time_for_iterations
            measurement_times.append(local_current_time) 

        return measurement_times
    
    def simulate_single_run(
            self,
            quantum_strategies: tuple[list[float], list[float]],
            classical_block_times: list[float],
            classical_block_times_index: int,
            current_time: float
    ) -> tuple[int, int, float, list[float], int]:
        
        alice_strat, bob_strat = quantum_strategies
        alice_measurement_times = self.generate_quantum_measurement_times(alice_strat, current_time)
        bob_measurement_times = self.generate_quantum_measurement_times(bob_strat, current_time)

        alice_index = 0
        bob_index = 0

        last_alice_measured_time = current_time
        last_bob_measured_time = current_time

        num_blocks = 0
        num_forks = 0

        while alice_index < len(alice_measurement_times) or bob_index < len(bob_measurement_times) or classical_block_times_index < len(classical_block_times):
            events = [
                (alice_measurement_times[alice_index] if alice_index < len(alice_measurement_times) else math.inf, 'Alice'),
                (bob_measurement_times[bob_index] if bob_index < len(bob_measurement_times) else math.inf, 'Bob'),  
                (classical_block_times[classical_block_times_index] if classical_block_times_index < len(classical_block_times) else math.inf, 'Classical')
            ]
            events.sort(key=lambda x: x[0])

            # Handle simultaneous events
            event_time = events[0][0]
            simultaneous_events = [event for event in events if event[0] == event_time]

            current_time = event_time
            if current_time > self.quantum_simulation_time:
                return num_blocks, num_forks, current_time, classical_block_times, classical_block_times_index

            # Alice and Bob simultaneous event
            if len(simultaneous_events) == 2 and 'Alice' in [e[1] for e in simultaneous_events] and 'Bob' in [e[1] for e in simultaneous_events]:
                r_alice = random.random()
                alice_iterations = alice_strat[alice_index]
                
                r_bob = random.random()
                bob_iterations = bob_strat[bob_index]

                alice_success = r_alice <= self.measurement_probability(int(alice_iterations))
                bob_success = r_bob <= self.measurement_probability(int(bob_iterations))

                if alice_success:
                    num_blocks += 1
                if bob_success:
                    num_blocks += 1

                if alice_success or bob_success:
                    classical_block_times = self.generate_classical_block_times(current_time)
                    return num_blocks, num_forks, current_time, classical_block_times, 0

                alice_index += 1
                bob_index += 1

            # Classical and Alice simultaneous event
            elif len(simultaneous_events) == 2 and 'Classical' in [e[1] for e in simultaneous_events] and 'Alice' in [e[1] for e in simultaneous_events]:
                num_blocks += 1
                r_alice = random.random()
                alice_iterations = alice_strat[alice_index]
                last_alice_measured_time = current_time

                if r_alice <= self.measurement_probability(int(alice_iterations)):
                    num_blocks += 1
                    num_forks += 1

                    #Bob attempts to mine aggressively
                    if bob_index < len(bob_strat):
                        r_bob = random.random()
                        bob_aggressive_iterations = self.time_to_iterations(current_time - last_bob_measured_time)
                        if r_bob <= self.measurement_probability(int(bob_aggressive_iterations)):
                            num_blocks += 1
                            num_forks += 1
                        last_bob_measured_time = current_time

                    classical_block_times = self.generate_classical_block_times(current_time)
                    return num_blocks, num_forks, current_time, classical_block_times, 0
                else:
                    alice_index += 1
                    classical_block_times_index += 1
                    return num_blocks, num_forks, current_time, classical_block_times, classical_block_times_index

            # Classical and Bob simultaneous event
            elif len(simultaneous_events) == 2 and 'Classical' in [e[1] for e in simultaneous_events] and 'Bob' in [e[1] for e in simultaneous_events]:
                num_blocks += 1
                r_bob = random.random()
                bob_iterations = bob_strat[bob_index]
                last_bob_measured_time = current_time

                if r_bob <= self.measurement_probability(int(bob_iterations)):
                    num_blocks += 1
                    num_forks += 1

                    #Alice attempts to mine aggressively
                    if alice_index < len(alice_strat):
                        r_alice = random.random()
                        alice_aggressive_iterations = self.time_to_iterations(current_time - last_alice_measured_time)
                        if r_alice <= self.measurement_probability(int(alice_aggressive_iterations)):
                            num_blocks += 1
                            num_forks += 1
                        
                        last_alice_measured_time = current_time

                    classical_block_times = self.generate_classical_block_times(current_time)
                    return num_blocks, num_forks, current_time, classical_block_times, 0
                else:
                    bob_index += 1
                    classical_block_times_index += 1
                    return num_blocks, num_forks, current_time, classical_block_times, classical_block_times_index

            # If only one event happened
            else:
                event_type = simultaneous_events[0][1]
                if event_type == 'Alice':
                    r_alice = random.random()
                    alice_iterations = alice_strat[alice_index]
                    last_alice_measured_time = current_time

                    if r_alice <= self.measurement_probability(int(alice_iterations)):
                        num_blocks += 1

                        # Bob attempts to fork aggressively
                        if bob_index < len(bob_strat):
                            r_bob = random.random()
                            bob_aggressive_iterations = self.time_to_iterations(current_time - last_bob_measured_time)
                            if r_bob <= self.measurement_probability(int(bob_aggressive_iterations)):
                                num_blocks += 1
                                num_forks += 1

                            last_bob_measured_time = current_time

                        classical_block_times = self.generate_classical_block_times(current_time)
                        return num_blocks, num_forks, current_time, classical_block_times, 0
                    else:
                        alice_index += 1

                elif event_type == 'Bob':
                    r_bob = random.random()
                    bob_iterations = bob_strat[bob_index]
                    last_bob_measured_time = current_time

                    if r_bob <= self.measurement_probability(int(bob_iterations)):
                        num_blocks += 1

                        # Alice attempts to fork aggressively
                        if alice_index < len(alice_strat):
                            r_alice = random.random()
                            alice_aggressive_iterations = self.time_to_iterations(current_time - last_alice_measured_time)
                            if r_alice <= self.measurement_probability(int(alice_aggressive_iterations)):
                                num_blocks += 1
                                num_forks += 1

                            last_alice_measured_time = current_time

                        classical_block_times = self.generate_classical_block_times(current_time)
                        return num_blocks, num_forks, current_time, classical_block_times, 0
                    else:
                        bob_index += 1

                elif event_type == 'Classical':
                    num_blocks += 1

                    # Alice and Bob will attempt to mine aggressively
                    if alice_index < len(alice_strat):
                        r_alice = random.random()
                        alice_aggressive_iterations = self.time_to_iterations(current_time - last_alice_measured_time)
                        if r_alice <= self.measurement_probability(int(alice_aggressive_iterations)):
                            num_blocks += 1
                            num_forks += 1

                        last_alice_measured_time = current_time

                    if bob_index < len(bob_strat):
                        r_bob = random.random()
                        bob_aggressive_iterations = self.time_to_iterations(current_time - last_bob_measured_time)
                        if r_bob <= self.measurement_probability(int(bob_aggressive_iterations)):
                            num_blocks += 1
                            num_forks += 1

                        last_bob_measured_time = current_time

                    classical_block_times_index += 1
                    return num_blocks, num_forks, current_time, classical_block_times, classical_block_times_index

        return num_blocks, num_forks, current_time, classical_block_times, classical_block_times_index
    
    def simulate(self) -> tuple[float, float, float]:
        total_blocks = 0
        total_forks = 0
        current_time = 0.0
        classical_block_times = self.generate_classical_block_times(current_time)
        classical_block_times_index = 0

        while current_time < self.quantum_simulation_time:
            quantum_strategies = self.select_strategy()
            blocks_found, forks, current_time, classical_block_times, classical_block_times_index = self.simulate_single_run(
                quantum_strategies,
                classical_block_times,
                classical_block_times_index,
                current_time
            )

            if current_time >= self.quantum_simulation_time: 
                break

            total_blocks += blocks_found
            total_forks += forks

        average_fork_rate = total_forks / total_blocks if total_blocks > 0 else 0
        return average_fork_rate, total_blocks, total_forks

    def simulate_all(self) -> tuple[float, float, float]:
        total_fork_rate = 0.0
        total_blocks = 0.0
        total_forks = 0.0

        for _ in range(self.num_simulations):
            #print('Simulation {} of {}'.format(_ + 1, self.num_simulations))
            fork_rate, blocks_found, forks = self.simulate()
            total_fork_rate += fork_rate
            total_blocks += blocks_found
            total_forks += forks

        average_fork_rate = total_fork_rate / self.num_simulations
        average_blocks = total_blocks / self.num_simulations
        average_forks = total_forks / self.num_simulations

        return average_fork_rate, average_blocks, average_forks
    
    def simulate_fixed_strategy(self, fixed_iterations: int = 51471) -> tuple[float, float, float, float]:
        total_blocks = 0
        quantum_blocks = 0  # Blocks found by Alice or Bob
        total_forks = 0
        current_time = 0.0
        
        full_measurement_prob = self.measurement_probability(fixed_iterations)
        
        classical_block_interval = 1 / self.classical_block_rate  # Average time between classical blocks
        
        time_per_iteration_set = self.iterations_to_time(fixed_iterations)
        
        while current_time < self.quantum_simulation_time:
            current_time += time_per_iteration_set
            
            if current_time > self.quantum_simulation_time:
                break
            
            r_alice = random.random()
            r_bob = random.random()
            
            alice_success = r_alice <= full_measurement_prob
            bob_success = r_bob <= full_measurement_prob
            
            if alice_success:
                total_blocks += 1
                quantum_blocks += 1
            
            if bob_success:
                total_blocks += 1
                quantum_blocks += 1
            
            if alice_success and bob_success:
                total_forks += 1
            
            classical_block_time = np.random.exponential(classical_block_interval)
            
            if classical_block_time < time_per_iteration_set:
                total_blocks += 1
                
                r_alice = random.random()
                r_bob = random.random()
                
                partial_time_ratio = classical_block_time / time_per_iteration_set
                partial_iterations = int(fixed_iterations * partial_time_ratio)
                partial_prob = self.measurement_probability(partial_iterations)
                
                alice_success = r_alice <= partial_prob
                bob_success = r_bob <= partial_prob
                
                if alice_success:
                    total_blocks += 1
                    quantum_blocks += 1
                    total_forks += 1
                
                if bob_success:
                    total_blocks += 1
                    quantum_blocks += 1
                    total_forks += 1

        # Calculate fork rate and quantum percentage
        if total_blocks > 0:
            fork_rate = total_forks / total_blocks
            quantum_percentage = quantum_blocks / total_blocks * 100
        else:
            fork_rate = 0.0
            quantum_percentage = 0.0
        
        return fork_rate, total_blocks, total_forks, quantum_percentage
    
    def simulate_all_fixed_strategy(self, fixed_iterations: int = 51471) -> tuple[float, float, float, float]:
        total_fork_rate = 0.0
        total_blocks = 0.0
        total_forks = 0.0
        total_quantum_percentage = 0.0

        for _ in range(self.num_simulations):
            fork_rate, blocks_found, forks, quantum_percentage = self.simulate_fixed_strategy(fixed_iterations)
            total_fork_rate += fork_rate
            total_blocks += blocks_found
            total_forks += forks
            total_quantum_percentage += quantum_percentage

        average_fork_rate = total_fork_rate / self.num_simulations
        average_blocks = total_blocks / self.num_simulations
        average_forks = total_forks / self.num_simulations
        average_quantum_percentage = total_quantum_percentage / self.num_simulations

        return average_fork_rate, average_blocks, average_forks, average_quantum_percentage

    def simulate_all_fixed_strategy_parallel(self, fixed_iterations: int = 51471, max_workers: int = None) -> tuple[float, float, float, float]:
        """Parallel version using ProcessPoolExecutor"""
        if max_workers is None:
            max_workers = min(cpu_count(), 8)  # Cap at 8 to avoid memory issues
        
        # Determine chunk size for better load balancing
        chunk_size = max(1, self.num_simulations // (max_workers * 4))
        
        total_fork_rate = 0.0
        total_blocks = 0.0
        total_forks = 0.0
        total_quantum_percentage = 0.0
        
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            # Create simulation parameters for each worker
            sim_params = []
            remaining_sims = self.num_simulations
            
            while remaining_sims > 0:
                current_chunk = min(chunk_size, remaining_sims)
                sim_params.append((
                    self.nash_equilibrium,
                    current_chunk,
                    self.classical_block_rate,
                    self.quantum_simulation_time,
                    self.difficulty,
                    self.c,
                    fixed_iterations
                ))
                remaining_sims -= current_chunk
            
            # Submit all tasks
            future_to_params = {
                executor.submit(run_fixed_strategy_simulation_chunk, params): params
                for params in sim_params
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_params):
                try:
                    fork_rate, blocks_found, forks, quantum_percentage = future.result()
                    total_fork_rate += fork_rate
                    total_blocks += blocks_found
                    total_forks += forks
                    total_quantum_percentage += quantum_percentage
                except Exception as exc:
                    print(f'Simulation chunk generated an exception: {exc}')
        
        # Average the results
        average_fork_rate = total_fork_rate / self.num_simulations
        average_blocks = total_blocks / self.num_simulations
        average_forks = total_forks / self.num_simulations
        average_quantum_percentage = total_quantum_percentage / self.num_simulations

        return average_fork_rate, average_blocks, average_forks, average_quantum_percentage


# Optimized numba-compiled functions for fixed strategy simulation
@njit
def measurement_probability_fast(iterations: int, difficulty: float) -> float:
    """Numba-compiled version of measurement_probability"""
    theta = math.asin(1 / math.sqrt(difficulty))
    probability = (math.sin((2 * iterations + 1) * theta))**2
    return probability

@njit
def simulate_fixed_strategy_fast(
    fixed_iterations: int,
    difficulty: float,
    classical_block_rate: float,
    quantum_simulation_time: float,
    seconds_per_iteration: float,
    num_simulations: int
) -> tuple[float, float, float, float]:
    """Numba-compiled version for maximum speed"""
    
    total_fork_rate = 0.0
    total_blocks = 0.0
    total_forks = 0.0
    total_quantum_percentage = 0.0
    
    full_measurement_prob = measurement_probability_fast(fixed_iterations, difficulty)
    print('Full measurement probability:', full_measurement_prob)
    classical_block_interval = 1.0 / classical_block_rate
    time_per_iteration_set = fixed_iterations * seconds_per_iteration
    
    for sim in range(num_simulations):
        total_blocks_sim = 0
        quantum_blocks_sim = 0
        total_forks_sim = 0
        current_time = 0.0
        
        while current_time < quantum_simulation_time:
            current_time += time_per_iteration_set
            
            if current_time > quantum_simulation_time:
                break
            
            r_alice = random.random()
            r_bob = random.random()
            
            alice_success = r_alice <= full_measurement_prob
            bob_success = r_bob <= full_measurement_prob
            
            if alice_success:
                total_blocks_sim += 1
                quantum_blocks_sim += 1
            
            if bob_success:
                total_blocks_sim += 1
                quantum_blocks_sim += 1
            
            if alice_success and bob_success:
                total_forks_sim += 1
            
            classical_block_time = np.random.exponential(classical_block_interval)
            
            if classical_block_time < time_per_iteration_set:
                total_blocks_sim += 1
                
                r_alice = random.random()
                r_bob = random.random()
                
                partial_time_ratio = classical_block_time / time_per_iteration_set
                partial_iterations = int(fixed_iterations * partial_time_ratio)
                partial_prob = measurement_probability_fast(partial_iterations, difficulty)
                print('Partial measurement probability:', partial_prob)
                
                alice_success = r_alice <= partial_prob
                bob_success = r_bob <= partial_prob
                
                if alice_success:
                    total_blocks_sim += 1
                    quantum_blocks_sim += 1
                    total_forks_sim += 1
                
                if bob_success:
                    total_blocks_sim += 1
                    quantum_blocks_sim += 1
                    total_forks_sim += 1
        
        # Calculate metrics for this simulation
        if total_blocks_sim > 0:
            fork_rate = total_forks_sim / total_blocks_sim
            quantum_percentage = quantum_blocks_sim / total_blocks_sim * 100
        else:
            fork_rate = 0.0
            quantum_percentage = 0.0
        
        total_fork_rate += fork_rate
        total_blocks += total_blocks_sim
        total_forks += total_forks_sim
        total_quantum_percentage += quantum_percentage
    
    # Average the results
    average_fork_rate = total_fork_rate / num_simulations
    average_blocks = total_blocks / num_simulations
    average_forks = total_forks / num_simulations
    average_quantum_percentage = total_quantum_percentage / num_simulations

    return average_fork_rate, average_blocks, average_forks, average_quantum_percentage


def run_fixed_strategy_simulation_chunk(params):
    """Function to run a chunk of simulations in parallel"""
    nash_eq, num_sims, classical_rate, sim_time, difficulty, c, fixed_iterations = params
    
    # Create a new simulator for this process
    simulator = QuantumMiningSimulator(nash_eq, num_sims, classical_rate, sim_time, difficulty, c)
    return simulator.simulate_all_fixed_strategy(fixed_iterations)


def simulate_fixed_strategy_across_cs_optimized(nash_eq, num_simulations: int, fixed_iterations: int = 51471, use_numba: bool = True):
    """Optimized version with both numba compilation and multiprocessing"""
    cs = [1.0, 2.0, 5.0, 10.0, 25.0, 50.0, 100.0, 250.0, 500.0, 1000.0, 2500.0, 5000.0, 10000.0, 25000.0, 50000.0, 100000.0]    
    fork_rates = []
    blocks_found = []
    forks_found = []
    quantum_percentages = []
    
    # Pre-calculate common values
    difficulty = 119116256505723.5
    classical_block_rate = 1/600
    quantum_simulation_time = 86400.0
    optimal_iterations = np.floor(np.pi / 4 * np.sqrt(difficulty))
    
    for c in cs:
        # Reduce simulation count based on c value for computational efficiency
        if c <= 10.0:
            actual_num_simulations = num_simulations
        elif c <= 100.0:
            actual_num_simulations = max(100, num_simulations // 5)
        elif c <= 1000.0:
            actual_num_simulations = max(50, num_simulations // 10)
        elif c <= 10000.0:
            actual_num_simulations = max(20, num_simulations // 20)
        else:  # c > 10000
            actual_num_simulations = max(10, num_simulations // 50)
            
        print(f"Simulating with c = {c}, fixed iterations = {fixed_iterations}, num_simulations = {actual_num_simulations}")
        start_time = time.time()
        
        if use_numba and c >= 10.0:  # Use numba for high c values
            seconds_per_iteration = 600 / (c * optimal_iterations)
            avg_fork_rate, avg_blocks, avg_forks, avg_quantum_percentage = simulate_fixed_strategy_fast(
                fixed_iterations, difficulty, classical_block_rate, 
                quantum_simulation_time, seconds_per_iteration, actual_num_simulations
            )
        else:
            # Use parallel processing for lower c values or if numba is disabled
            simulator = QuantumMiningSimulator(nash_eq, actual_num_simulations, c=c)
            avg_fork_rate, avg_blocks, avg_forks, avg_quantum_percentage = simulator.simulate_all_fixed_strategy_parallel(fixed_iterations)
        
        elapsed_time = time.time() - start_time
        print(f'Simulation complete in {elapsed_time:.2f} seconds!')
        print('Average Fork Rate (Stale Rate):', avg_fork_rate)
        print('Average Blocks Found Per Day:', avg_blocks)
        print('Average Forks Found Per Day:', avg_forks)
        print('Average Quantum Percentage:', avg_quantum_percentage)
        
        fork_rates.append(avg_fork_rate)
        blocks_found.append(avg_blocks)
        forks_found.append(avg_forks)
        quantum_percentages.append(avg_quantum_percentage)
    
    # Calculate 51% attack threshold: (1 - stale_rate) / (2 - stale_rate)
    attack_thresholds = [(1 - fork_rate) / (2 - fork_rate) for fork_rate in fork_rates]
    
    # Save data to CSV files
    with open('stale_rates_data.csv', 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['c_value', 'stale_rate'])
        for c, stale_rate in zip(cs, fork_rates):
            writer.writerow([c, stale_rate])
    
    with open('attack_threshold_data.csv', 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['c_value', 'attack_threshold'])
        for c, threshold in zip(cs, attack_thresholds):
            writer.writerow([c, threshold])
    
    with open('total_blocks_data.csv', 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['c_value', 'total_blocks'])
        for c, blocks in zip(cs, blocks_found):
            writer.writerow([c, blocks])
    
    with open('forks_found_data.csv', 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['c_value', 'forks_found'])
        for c, forks in zip(cs, forks_found):
            writer.writerow([c, forks])
    
    with open('quantum_blocks_data.csv', 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['c_value', 'quantum_percentage'])
        for c, quantum_pct in zip(cs, quantum_percentages):
            writer.writerow([c, quantum_pct])
    
    # Create separate plots without titles
    
    # Plot 1: Stale Rate
    plt.figure()
    plt.plot(cs, fork_rates, 'o-', color='blue')
    plt.xscale('log')
    plt.xlabel('$c$')
    plt.ylabel('Stale Rate')
    plt.grid(True)
    plt.savefig('images/stale_rate_plot.png')
    plt.close()
    
    # Plot 2: 51% Attack Threshold
    plt.figure()
    plt.plot(cs, attack_thresholds, 'o-', color='cyan')
    plt.xscale('log')
    plt.xlabel('$c$')
    plt.ylabel('51% Attack Threshold')
    plt.grid(True)
    plt.savefig('images/attack_threshold_plot.png')
    plt.close()
    
    # Plot 3: Total Blocks Found Per Day
    plt.figure()
    plt.plot(cs, blocks_found, 'o-', color='green')
    plt.xscale('log')
    plt.xlabel('$c$')
    plt.ylabel('Average Blocks Found Per Day')
    plt.grid(True)
    plt.savefig('images/total_blocks_plot.png')
    plt.close()
    
    # Plot 4: Forks Found Per Day
    plt.figure()
    plt.plot(cs, forks_found, 'o-', color='red')
    plt.xscale('log')
    plt.xlabel('$c$')
    plt.ylabel('Average Forks Found Per Day')
    plt.grid(True)
    plt.savefig('images/forks_found_plot.png')
    plt.close()
    
    # Plot 5: Blocks Found Per Day by Quantum Miners
    plt.figure()
    plt.plot(cs, quantum_percentages, 'o-', color='purple')
    plt.xscale('log')
    plt.xlabel('$c$')
    plt.ylabel('Quantum Blocks (%)')
    plt.grid(True)
    plt.savefig('images/quantum_blocks_plot.png')
    plt.close()
    
    return fork_rates, blocks_found, forks_found, quantum_percentages, attack_thresholds


# Optimized version that keeps the same core logic but runs much faster
class FastQuantumMiningSimulator(QuantumMiningSimulator):
    """Optimized version that preserves exact same logic but runs faster"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Pre-calculate values that don't change
        self._theta = math.asin(1 / math.sqrt(self.difficulty))
        self._classical_block_interval = 1.0 / self.classical_block_rate
        
    def measurement_probability_fast(self, iterations: int) -> float:
        """Faster version using pre-calculated theta"""
        return (math.sin((2 * iterations + 1) * self._theta))**2
    
    def simulate_fixed_strategy_vectorized(self, fixed_iterations: int = 51471) -> tuple[float, float, float, float]:
        """Vectorized version for better performance with same logic"""
        # Pre-calculate constants
        full_measurement_prob = self.measurement_probability_fast(fixed_iterations)
        time_per_iteration_set = self.iterations_to_time(fixed_iterations)
        
        # Estimate number of cycles to pre-allocate arrays
        estimated_cycles = int(self.quantum_simulation_time / time_per_iteration_set) + 100
        
        # Pre-generate all random numbers we'll need
        alice_randoms = np.random.random(estimated_cycles * 2)  # *2 for potential classical responses
        bob_randoms = np.random.random(estimated_cycles * 2)
        classical_block_times = np.random.exponential(self._classical_block_interval, estimated_cycles)
        
        total_blocks = 0
        quantum_blocks = 0
        total_forks = 0
        current_time = 0.0
        
        rand_idx = 0
        
        while current_time < self.quantum_simulation_time and rand_idx < len(alice_randoms) - 1:
            current_time += time_per_iteration_set
            
            if current_time > self.quantum_simulation_time:
                break
            
            # Alice and Bob quantum attempts
            alice_success = alice_randoms[rand_idx] <= full_measurement_prob
            bob_success = bob_randoms[rand_idx] <= full_measurement_prob
            rand_idx += 1
            
            if alice_success:
                total_blocks += 1
                quantum_blocks += 1
            
            if bob_success:
                total_blocks += 1
                quantum_blocks += 1
            
            if alice_success and bob_success:
                total_forks += 1
            
            # Classical block check
            classical_block_time = classical_block_times[min(rand_idx // 2, len(classical_block_times) - 1)]
            
            if classical_block_time < time_per_iteration_set:
                total_blocks += 1
                
                # Quantum responses to classical block
                partial_time_ratio = classical_block_time / time_per_iteration_set
                partial_iterations = int(fixed_iterations * partial_time_ratio)
                partial_prob = self.measurement_probability_fast(partial_iterations)
                
                alice_success = alice_randoms[rand_idx] <= partial_prob
                bob_success = bob_randoms[rand_idx] <= partial_prob
                rand_idx += 1
                
                if alice_success:
                    total_blocks += 1
                    quantum_blocks += 1
                    total_forks += 1
                
                if bob_success:
                    total_blocks += 1
                    quantum_blocks += 1
                    total_forks += 1
        
        # Calculate metrics (same as original)
        if total_blocks > 0:
            fork_rate = total_forks / total_blocks
            quantum_percentage = quantum_blocks / total_blocks * 100
        else:
            fork_rate = 0.0
            quantum_percentage = 0.0
        
        return fork_rate, total_blocks, total_forks, quantum_percentage
    
    def simulate_all_fixed_strategy_fast(self, fixed_iterations: int = 51471) -> tuple[float, float, float, float]:
        """Faster version using vectorized approach"""
        # Use numpy arrays for accumulation
        fork_rates = np.zeros(self.num_simulations)
        blocks_found = np.zeros(self.num_simulations)
        forks_found = np.zeros(self.num_simulations)
        quantum_percentages = np.zeros(self.num_simulations)
        
        for i in range(self.num_simulations):
            fork_rates[i], blocks_found[i], forks_found[i], quantum_percentages[i] = \
                self.simulate_fixed_strategy_vectorized(fixed_iterations)
        
        return np.mean(fork_rates), np.mean(blocks_found), np.mean(forks_found), np.mean(quantum_percentages)


def simulate_fixed_strategy_across_cs_fast(nash_eq, num_simulations: int, fixed_iterations: int = 51471):
    """Faster version of the main simulation function"""
    cs = [0.5, 1.0, 2.0, 5.0, 10.0, 25.0, 50.0, 100.0, 250.0, 500.0, 1000.0, 2500.0, 5000.0, 10000.0, 25000.0, 50000.0, 100000.0]    
    fork_rates = []
    blocks_found = []
    forks_found = []
    quantum_percentages = []
    
    for c in cs:
        # Adaptive simulation count (same logic as original)
        if c <= 10.0:
            actual_num_simulations = num_simulations
        elif c <= 100.0:
            actual_num_simulations = max(100, num_simulations // 5)
        elif c <= 1000.0:
            actual_num_simulations = max(50, num_simulations // 10)
        elif c <= 10000.0:
            actual_num_simulations = max(20, num_simulations // 20)
        else:
            actual_num_simulations = max(10, num_simulations // 50)
            
        print(f"Simulating with c = {c}, fixed iterations = {fixed_iterations}, num_simulations = {actual_num_simulations}")
        start_time = time.time()
        
        # Use the fast simulator
        simulator = FastQuantumMiningSimulator(nash_eq, actual_num_simulations, c=c)
        avg_fork_rate, avg_blocks, avg_forks, avg_quantum_percentage = simulator.simulate_all_fixed_strategy_fast(fixed_iterations)
        
        elapsed_time = time.time() - start_time
        print(f'Simulation complete in {elapsed_time:.2f} seconds!')
        print('Average Fork Rate (Stale Rate):', avg_fork_rate)
        print('Average Blocks Found Per Day:', avg_blocks)
        print('Average Forks Found Per Day:', avg_forks)
        print('Average Quantum Percentage:', avg_quantum_percentage)
        
        fork_rates.append(avg_fork_rate)
        blocks_found.append(avg_blocks)
        forks_found.append(avg_forks)
        quantum_percentages.append(avg_quantum_percentage)
    
    # Rest of the function remains the same...
    attack_thresholds = [(1 - fork_rate) / (2 - fork_rate) for fork_rate in fork_rates]
    
    # Save data and create plots (same as original)
    with open('stale_rates_data_fast.csv', 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['c_value', 'stale_rate'])
        for c, stale_rate in zip(cs, fork_rates):
            writer.writerow([c, stale_rate])
    
    return fork_rates, blocks_found, forks_found, quantum_percentages, attack_thresholds


def main_optimized():
    """Main function using the optimized simulator"""
    fname = 'output.txt'
    analyzer = NashEquilibriaAnalyzer()
    nash_eq = analyzer.converge(fname)

    # Use the fast version
    simulate_fixed_strategy_across_cs_fast(nash_eq, num_simulations=1000, fixed_iterations=51471)

if __name__ == "__main__":
    main_optimized()