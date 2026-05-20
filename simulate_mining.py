from analyze_nasheqs import NashEquilibriaAnalyzer
import numpy as np
import random
import math
from buildpayoff import BuildPayoff
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
from mpl_toolkits.mplot3d import Axes3D
import pandas as pd
from multiprocessing import Pool
import os

_sim_worker = None

def _init_sim_worker(sim):
    global _sim_worker
    _sim_worker = sim

def _run_one_simulation(_):
    return _sim_worker.simulate()


class QuantumMiningSimulator:
    def __init__(self,
                 nash_equilibrium: dict[str, list[tuple[list[float], float]]],
                 num_simulations: int = 100000,
                 classical_block_rate: float = 1/600, #blocks per second: 1 every 10 minutes
                 quantum_simulation_time: float = 86400.0, #seconds in a day
                 difficulty: float = 119116256505723.5, #current difficulty
                 #difficulty: float = 3651011.631, #difficulty from 2013 (low D)
                 scale_with_D: bool = False
    ) -> None:
        self.nash_equilibrium = nash_equilibrium
        self.num_simulations = num_simulations
        self.classical_block_rate = classical_block_rate
        self.quantum_simulation_time = quantum_simulation_time
        self.difficulty = difficulty
        self.scale_with_D = scale_with_D
        if not scale_with_D:
            self.optimal_iterations = min(np.floor(np.pi / 4 * np.sqrt(difficulty)),  int(np.floor(np.pi/4 * np.sqrt(2**32))))
        else:
            self.optimal_iterations = np.floor(np.pi / 4 * np.sqrt(difficulty))

        self.seconds_per_iteration = 600 / (self.optimal_iterations)
        self._theta = math.asin(1 / math.sqrt(self.difficulty))
        self._measurement_cache = {}
        alice_strats = nash_equilibrium['Alice']
        bob_strats = nash_equilibrium['Bob']
        self._alice_strats = [s[0] for s in alice_strats]
        self._alice_weights = [s[1] for s in alice_strats]
        self._bob_strats = [s[0] for s in bob_strats]
        self._bob_weights = [s[1] for s in bob_strats]

    def measurement_probability(self, iterations: int) -> float:
        if iterations not in self._measurement_cache:
            self._measurement_cache[iterations] = (math.sin((2 * iterations + 1) * self._theta))**2
        return self._measurement_cache[iterations]
    
    def select_strategy(self) -> tuple[list[float], list[float]]:
        return (
            random.choices(self._alice_strats, weights=self._alice_weights)[0],
            random.choices(self._bob_strats, weights=self._bob_weights)[0]
        )

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
            # Handle simultaneous events
            event_time = min(events, key=lambda x: x[0])[0]
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
                if alice_success and bob_success:
                    num_forks += 1

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

                    #Bob employs the AQMS
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

                    #Alice employs the AQMS
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

                        # Bob employs the AQMS
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

                        # Alice employs the AQMS
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

                    # Alice and Bob will employ the AQMS
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

        average_fork_rate = total_forks / total_blocks
        return average_fork_rate, total_blocks, total_forks

    def simulate_all(self) -> tuple[float, float, float]:
        n_workers = min(os.cpu_count() or 1, self.num_simulations)
        print_interval = max(1, self.num_simulations // 10)
        total_blocks = 0
        total_forks = 0

        with Pool(processes=n_workers, initializer=_init_sim_worker, initargs=(self,)) as pool:
            for i, result in enumerate(pool.imap_unordered(_run_one_simulation, range(self.num_simulations)), 1):
                total_blocks += result[1]
                total_forks += result[2]
                if i % print_interval == 0:
                    print(f"  {i}/{self.num_simulations} simulations complete ({100 * i // self.num_simulations}%)")

        average_fork_rate = total_forks / total_blocks if total_blocks > 0 else 0.0
        average_blocks = total_blocks / self.num_simulations
        average_forks = total_forks / self.num_simulations

        return average_fork_rate, average_blocks, average_forks

def format_func(x, pos):
    return f'$2^{{{int(np.log2(x))}}}$'

def simulate_multiple_strategies(num_simulations=10000, results_dir='.', images_dir='images'):
    strategies = [
        {'num_plays': 1, 'n_q': 50, 'label': r'$c=1$', 'color': 'blue', 'marker': 'o'},
        {'num_plays': 2, 'n_q': 25, 'label': r'$c=2$', 'color': 'red', 'marker': 's'},
        {'num_plays': 3, 'n_q': 15, 'label': r'$c=3$', 'color': 'green', 'marker': '^'},
        {'num_plays': 4, 'n_q': 15, 'label': r'$c=4$', 'color': 'purple', 'marker': 'd'}
    ]

    difficulties = [2**30, 2**31, 2**32, 2**33, 2**34, 2**35, 2**36, 2**37, 2**38, 2**39, 2**40, 2**41, 2**42, 2**43, 2**44, 2**45]

    clustering_factor = 2.0
    gamma = 0.5

    import os, tempfile
    os.makedirs(results_dir, exist_ok=True)
    os.makedirs(images_dir, exist_ok=True)

    fig, ax = plt.subplots(figsize=(10, 6))

    for strategy in strategies:
        num_plays = strategy['num_plays']
        n_q = strategy['n_q']
        print(f"\n{'='*60}")
        print(f"Processing strategy: c={num_plays}, n_q={n_q}")
        print(f"{'='*60}")

        fork_rates = []
        csv_data = []

        for difficulty in difficulties:
            print(f"Difficulty: 2^{int(np.log2(difficulty))}")

            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as tmp:
                out_fname = tmp.name

            try:
                payoff_builder = BuildPayoff(n_q, num_plays, difficulty, clustering_factor, gamma, out_fname, scale_with_D=False)
                A = payoff_builder.get_payoff()
                B = payoff_builder.get_payoff(bob=True)

                payoff_builder.get_nash_eq_pygambit(A, B)
                print('Nash equilibrium found!')

                analyzer = NashEquilibriaAnalyzer()
                nash_eq = analyzer.converge(out_fname)

                print('Beginning simulation...')
                simulator = QuantumMiningSimulator(nash_eq, num_simulations, difficulty=difficulty)
                avg_fork_rate, avg_blocks, avg_forks = simulator.simulate_all()
                print(f'Average Stale Rate: {avg_fork_rate}')

                fork_rates.append(avg_fork_rate)

                csv_data.append({
                    'difficulty': difficulty,
                    'log2_difficulty': int(np.log2(difficulty)),
                    'stale_rate': avg_fork_rate,
                    'threshold': (1 - avg_fork_rate) / (2 - avg_fork_rate),
                    'avg_blocks': avg_blocks,
                    'avg_forks': avg_forks
                })
            finally:
                if os.path.exists(out_fname):
                    os.remove(out_fname)

        csv_filename = os.path.join(results_dir, f'simulation_difficulties_c{num_plays}.csv')
        df = pd.DataFrame(csv_data)
        df.to_csv(csv_filename, index=False)
        print(f"\nData saved to: {csv_filename}")

        ax.plot(difficulties, fork_rates,
                marker=strategy['marker'],
                linestyle='-',
                color=strategy['color'],
                label=strategy['label'],
                linewidth=2,
                markersize=8)

    ax.set_xscale('log', base=2)
    ax.xaxis.set_major_formatter(FuncFormatter(format_func))
    ax.set_xlabel(r'$D$', fontsize=12)
    ax.set_ylabel(r'$p_\text{stale}$', fontsize=12)
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=10, loc='best')

    plt.tight_layout()
    plot_path = os.path.join(images_dir, 'stale_rate_vs_difficulty_all_strategies.pdf')
    plt.savefig(plot_path, dpi=300)
    plt.show()

    print(f"\n{'='*60}")
    print("All simulations complete!")
    print(f"{'='*60}")

def main():
    fname = 'output.txt'
    analyzer = NashEquilibriaAnalyzer()
    nash_eq = analyzer.converge(fname)

    #D = 119116256505723.5 #difficulty as of May 9 2025
    D = 3651011.631 #difficulty as of Feb 26 2013

    num_simulations = 1000000
    simulator = QuantumMiningSimulator(nash_eq, num_simulations = num_simulations, difficulty = D, scale_with_D = False)
    print('Simulating {} runs...'.format(num_simulations))
    avg_fork_rate, avg_blocks, avg_forks = simulator.simulate_all()
    print('Simulation complete!')
    print('Average Stale Rate:', avg_fork_rate)
    print('Average Blocks Found Per Day:', avg_blocks)
    print('Average Forks Found Per Day:', avg_forks)
    
    
    #simulate_multiple_strategies()
    
if __name__  == '__main__':
    main()