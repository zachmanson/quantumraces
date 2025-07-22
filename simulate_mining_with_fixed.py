from analyze_nasheqs import NashEquilibriaAnalyzer
import numpy as np
import random
import math
from buildpayoffgambit import BuildPayoff
import matplotlib.pyplot as plt
from multiprocessing import Pool, cpu_count


class QuantumMiningSimulator:
    def __init__(self,
                 nash_equilibrium: dict[str, list[tuple[list[float], float]]],
                 num_simulations: int = 100000,
                 classical_block_rate: float = 1/600, #blocks per second: 1 every 10 minutes
                 quantum_simulation_time: float = 86400.0, #seconds in a day
                 difficulty: float = 119116256505723.5, #current difficulty
                 #difficulty: float = 3651011.631, #difficulty from 2013 (low D)
                 beta: float = 1.0 #fraction of optimal iterations
    ) -> None:
        self.nash_equilibrium = nash_equilibrium
        self.num_simulations = num_simulations
        self.classical_block_rate = classical_block_rate
        self.quantum_simulation_time = quantum_simulation_time
        self.difficulty = difficulty
        self.optimal_iterations = np.floor(np.pi / 4 * np.sqrt(difficulty))
        self.seconds_per_iteration = 600 / (beta * self.optimal_iterations)

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
    
    def simulate_fixed_strategy(self, fixed_iterations: int = 51471) -> tuple[float, float, float]:
        total_blocks = 0
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
            
            if bob_success:
                total_blocks += 1
            
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
                    total_forks += 1
                
                if bob_success:
                    total_blocks += 1
                    total_forks += 1

        # Calculate fork rate
        if total_blocks > 0:
            fork_rate = total_forks / total_blocks
        else:
            fork_rate = 0.0
        
        return fork_rate, total_blocks, total_forks
    
    def simulate_all_fixed_strategy(self, fixed_iterations: int = 51471) -> tuple[float, float, float]:
        total_fork_rate = 0.0
        total_blocks = 0.0
        total_forks = 0.0

        for _ in range(self.num_simulations):
            fork_rate, blocks_found, forks = self.simulate_fixed_strategy(fixed_iterations)
            total_fork_rate += fork_rate
            total_blocks += blocks_found
            total_forks += forks

        average_fork_rate = total_fork_rate / self.num_simulations
        average_blocks = total_blocks / self.num_simulations
        average_forks = total_forks / self.num_simulations

        return average_fork_rate, average_blocks, average_forks


def run_fixed_strategy_simulation(args):
    simulator, fixed_iterations = args
    return simulator.simulate_fixed_strategy(fixed_iterations)


def simulate_across_betas(K: int, num_plays: int, D: float, clustering_factor: int, gamma: float, out_fname: str, num_simulations: int):
    betas = [0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 2.0]
    fork_rates = []
    for beta in betas:
        print(beta)
        payoff_builder = BuildPayoff(K, num_plays, D, clustering_factor, gamma, beta, out_fname)
        A = payoff_builder.get_payoff()
        B = payoff_builder.get_payoff(bob = True)

        payoff_builder.get_nash_eq_pygambit(A, B)

        print('Nash equilibrium found!')
        analyzer = NashEquilibriaAnalyzer()
        nash_eq = analyzer.converge(out_fname)

        print('Beginning simulation...')
        simulator = QuantumMiningSimulator(nash_eq, num_simulations, beta = beta)
        avg_fork_rate, avg_blocks, avg_forks = simulator.simulate_all()
        print('Simulation complete!')
        print('Average Fork Rate:', avg_fork_rate)
        fork_rates.append(avg_fork_rate)

    plt.plot(betas, fork_rates, 'o-')
    plt.xlabel('Fraction of optimal iterations')
    plt.ylabel('Average Fork Rate')
    plt.title('Network fork rate due to quantum mining')
    plt.grid(True)
    plt.savefig('fork_rate_vs_beta_fixed.png')


# Properly structured for multiprocessing support (if desired)
def simulate_fixed_strategy_across_betas(nash_eq, num_simulations: int, fixed_iterations: int = 51471):
    betas = [0.5, 1.0, 2.0, 5.0, 10.0, 25.0, 50.0, 100.0, 250.0, 500.0, 1000.0, 2500.0, 5000.0, 10000.0, 25000.0, 50000.0, 100000.0]    
    fork_rates = []
    blocks_found = []
    forks_found = []
    
    for beta in betas:
        print(f"Simulating with beta = {beta}, fixed iterations = {fixed_iterations}")
        simulator = QuantumMiningSimulator(nash_eq, num_simulations, beta=beta)
        
        # Single-threaded approach
        avg_fork_rate, avg_blocks, avg_forks = simulator.simulate_all_fixed_strategy(fixed_iterations)
        
        """
        # Alternative with multiprocessing at module level - uncomment if needed, but needs more testing
        with Pool(processes=cpu_count()) as pool:
            args = [(simulator, fixed_iterations) for _ in range(num_simulations)]
            results = pool.map(run_fixed_strategy_simulation, args)
            
            total_fork_rate = sum(res[0] for res in results)
            total_blocks = sum(res[1] for res in results)
            total_forks = sum(res[2] for res in results)
            
            avg_fork_rate = total_fork_rate / num_simulations
            avg_blocks = total_blocks / num_simulations
            avg_forks = total_forks / num_simulations
        """
        
        print('Simulation complete!')
        print('Average Fork Rate:', avg_fork_rate)
        print('Average Blocks Found Per Day:', avg_blocks)
        print('Average Forks Found Per Day:', avg_forks)
        
        fork_rates.append(avg_fork_rate)
        blocks_found.append(avg_blocks)
        forks_found.append(avg_forks)
    
    # Plot results
    plt.figure(figsize=(12, 8))
    
    plt.subplot(2, 2, 1)
    plt.plot(betas, fork_rates, 'o-', color='blue')
    plt.xscale('log')  # Log scale for better visualization
    plt.xlabel('Fraction of optimal iterations (beta)')
    plt.ylabel('Average Fork Rate')
    plt.title('Network fork rate with fixed iterations')
    plt.grid(True)
    
    plt.subplot(2, 2, 2)
    plt.plot(betas, blocks_found, 'o-', color='green')
    plt.xscale('log')
    plt.xlabel('Fraction of optimal iterations (beta)')
    plt.ylabel('Average Blocks Found Per Day')
    plt.title('Blocks per day with fixed iterations')
    plt.grid(True)
    
    plt.subplot(2, 2, 3)
    plt.plot(betas, forks_found, 'o-', color='red')
    plt.xscale('log')
    plt.xlabel('Fraction of optimal iterations (beta)')
    plt.ylabel('Average Forks Found Per Day')
    plt.title('Forks per day with fixed iterations')
    plt.grid(True)
    
    plt.tight_layout()
    plt.savefig('fixed_strategy_results.png')
    
    return fork_rates, blocks_found, forks_found
    
    
def main():
    fname = 'output.txt'
    analyzer = NashEquilibriaAnalyzer()
    nash_eq = analyzer.converge(fname)

    '''
    # Original simulation
    simulator = QuantumMiningSimulator(nash_eq, num_simulations=100000)
    print('Simulating {} runs with normal strategies...'.format(100000))
    avg_fork_rate, avg_blocks, avg_forks = simulator.simulate_all()
    print('Simulation complete!')
    print('Average Fork Rate:', avg_fork_rate)
    print('Average Blocks Found Per Day:', avg_blocks)
    print('Average Forks Found Per Day:', avg_forks)
    
    
    # Fixed strategy simulation
    print('\nSimulating with fixed strategy (51471 iterations)...')
    fixed_avg_fork_rate, fixed_avg_blocks, fixed_avg_forks = simulator.simulate_all_fixed_strategy(51471)
    print('Fixed strategy simulation complete!')
    print('Fixed Strategy Average Fork Rate:', fixed_avg_fork_rate)
    print('Fixed Strategy Average Blocks Found Per Day:', fixed_avg_blocks)
    print('Fixed Strategy Average Forks Found Per Day:', fixed_avg_forks)
    
    # Compare the results
    print('\nComparison:')
    print(f'Fork Rate: Nash strategy: {avg_fork_rate:.6f}, Fixed strategy: {fixed_avg_fork_rate:.6f}')
    print(f'Blocks: Nash strategy: {avg_blocks:.2f}, Fixed strategy: {fixed_avg_blocks:.2f}') 
    print(f'Forks: Nash strategy: {avg_forks:.2f}, Fixed strategy: {fixed_avg_forks:.2f}')
    
    # Uncomment to run beta analysis
    '''
    simulate_fixed_strategy_across_betas(nash_eq, num_simulations=10000)

    '''
    simulate_across_betas(
        K = 10,
        num_plays = 2,
        D = 82047028459932.62,
        clustering_factor = 2.0,
        gamma = 0.5,
        out_fname = 'betas_output.txt',
        num_simulations = 10000
    )
    ''' 


if __name__  == '__main__':
    main()