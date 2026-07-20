from analyze_nasheqs import NashEquilibriaAnalyzer
import numpy as np
import random
import math
from buildpayoff import BuildPayoff
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import pandas as pd
from multiprocessing import Pool
import os
from scipy.stats import binom as _binom

CLASSICAL_STALE_RATE = 0.0024


def _proportion_ci(p: float, n: int, z: float = 1.96) -> tuple:
    # Wilson interval — well-behaved when p is near 0 or 1
    z2 = z * z
    centre = (p + z2 / (2 * n)) / (1 + z2 / n)
    half = (z / (1 + z2 / n)) * math.sqrt(p * (1 - p) / n + z2 / (4 * n * n))
    return max(0.0, centre - half), min(1.0, centre + half)

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

    def simulate_all(self, csv_path: str = None) -> dict:
        n_workers = min(os.cpu_count() or 1, self.num_simulations)
        print_interval = max(1, self.num_simulations // 10)
        stale_rates = []
        all_blocks = []
        all_forks = []

        with Pool(processes=n_workers, initializer=_init_sim_worker, initargs=(self,)) as pool:
            for i, result in enumerate(pool.imap_unordered(_run_one_simulation, range(self.num_simulations)), 1):
                stale_rates.append(result[0])
                all_blocks.append(result[1])
                all_forks.append(result[2])
                if i % print_interval == 0:
                    print(f"  {i}/{self.num_simulations} simulations complete ({100 * i // self.num_simulations}%)")

        stale_rates = np.array(stale_rates)
        all_blocks = np.array(all_blocks, dtype=np.int64)
        all_forks = np.array(all_forks, dtype=np.int64)
        n = len(stale_rates)

        # Per-simulation binomial p-value: P(X >= forks | X ~ Binom(blocks, classical_rate))
        p_values = _binom.sf(all_forks - 1, all_blocks, CLASSICAL_STALE_RATE)

        self._last_stale_rates = stale_rates
        self._last_blocks = all_blocks
        self._last_forks = all_forks
        self._last_p_values = p_values

        prob_over_third = float(np.mean(stale_rates > 1/3))
        detection_prob = float(np.mean(p_values < 0.05))

        ci_third = _proportion_ci(prob_over_third, n)
        ci_detect = _proportion_ci(detection_prob, n)

        if csv_path:
            csv_dir = os.path.dirname(csv_path)
            if csv_dir:
                os.makedirs(csv_dir, exist_ok=True)
            pd.DataFrame({
                'stale_rate': stale_rates,
                'total_blocks': all_blocks,
                'total_forks': all_forks,
                'p_value': p_values,
            }).to_csv(csv_path, index=False)
            print(f"  Raw data saved to: {csv_path}")

        return {
            'mean_stale_rate': float(np.mean(stale_rates)),
            'std_stale_rate': float(np.std(stale_rates)),
            'p95_stale_rate': float(np.percentile(stale_rates, 95)),
            'p99_stale_rate': float(np.percentile(stale_rates, 99)),
            'max_stale_rate': float(np.max(stale_rates)),
            'prob_stale_over_third': prob_over_third,
            'prob_stale_over_third_ci': ci_third,
            'detection_prob_05': detection_prob,
            'detection_prob_05_ci': ci_detect,
            'avg_blocks': float(np.mean(all_blocks)),
            'avg_forks': float(np.mean(all_forks)),
        }

def simulate_multiple_strategies(num_simulations=10000, results_dir='.', images_dir='images', data_dir='data'):
    strategies = [
        {'num_plays': 1, 'n_q': 51, 'label': r'$c=1$'},
        {'num_plays': 2, 'n_q': 26, 'label': r'$c=2$'},
        {'num_plays': 3, 'n_q': 16, 'label': r'$c=3$'},
        {'num_plays': 4, 'n_q': 16, 'label': r'$c=4$'},
    ]

    difficulties = [2**30, 2**31, 2**32, 2**33, 2**34, 2**35, 2**36, 2**37, 2**38, 2**39, 2**40, 2**41, 2**42, 2**43, 2**44, 2**45]

    clustering_factor = 2.0
    gamma = 0.5

    os.makedirs(results_dir, exist_ok=True)
    os.makedirs(images_dir, exist_ok=True)
    os.makedirs(data_dir, exist_ok=True)
    nash_dir = os.path.join(data_dir, 'difficulty_sweep_nash_eqs')
    os.makedirs(nash_dir, exist_ok=True)

    colors  = {1: 'C0', 2: 'C1', 3: 'C2', 4: 'C3'}
    markers = {1: 'o',  2: 's',  3: '^',  4: 'd'}
    x_formatter = FuncFormatter(lambda x, _: f'$2^{{{int(np.log2(x))}}}$')

    all_rows = []
    all_raw = []
    all_p95s = {}
    all_detect_probs = {}

    for strategy in strategies:
        num_plays = strategy['num_plays']
        n_q = strategy['n_q']
        print(f"\n{'='*60}")
        print(f"Processing strategy: c={num_plays}, n_q={n_q}")
        print(f"{'='*60}")

        p95s = []
        detect_probs = []

        for difficulty in difficulties:
            log2_d = int(np.log2(difficulty))
            print(f"Difficulty: 2^{log2_d}")

            nash_fname = os.path.join(nash_dir, f'nash_eq_c{num_plays}_D{log2_d}.txt')

            payoff_builder = BuildPayoff(n_q, num_plays, difficulty, clustering_factor, gamma, nash_fname, scale_with_D=False)
            A = payoff_builder.get_payoff()
            B = payoff_builder.get_payoff(bob=True)

            payoff_builder.get_nash_eq_pygambit(A, B)
            print('Nash equilibrium found!')

            analyzer = NashEquilibriaAnalyzer()
            nash_eq = analyzer.converge(nash_fname)

            print('Beginning simulation...')
            simulator = QuantumMiningSimulator(nash_eq, num_simulations, difficulty=difficulty)
            stats = simulator.simulate_all()

            raw_df = pd.DataFrame({
                'c': num_plays,
                'log2_difficulty': log2_d,
                'stale_rate': simulator._last_stale_rates,
                'total_blocks': simulator._last_blocks,
                'total_forks': simulator._last_forks,
                'p_value': simulator._last_p_values,
            })
            all_raw.append(raw_df)
            print(f'P95 stale rate:      {stats["p95_stale_rate"]:.6f}')
            print(f'Detection prob:      {stats["detection_prob_05"]:.6f}')

            p95s.append(stats['p95_stale_rate'])
            detect_probs.append(stats['detection_prob_05'])

            all_rows.append({
                'c': num_plays,
                'difficulty': difficulty,
                'log2_difficulty': log2_d,
                'nash_eq_file': nash_fname,
                'mean_stale_rate': stats['mean_stale_rate'],
                'std_stale_rate': stats['std_stale_rate'],
                'p95_stale_rate': stats['p95_stale_rate'],
                'p99_stale_rate': stats['p99_stale_rate'],
                'max_stale_rate': stats['max_stale_rate'],
                'prob_stale_over_third': stats['prob_stale_over_third'],
                'prob_stale_over_third_ci_lower': stats['prob_stale_over_third_ci'][0],
                'prob_stale_over_third_ci_upper': stats['prob_stale_over_third_ci'][1],
                'detection_prob_05': stats['detection_prob_05'],
                'detection_prob_05_ci_lower': stats['detection_prob_05_ci'][0],
                'detection_prob_05_ci_upper': stats['detection_prob_05_ci'][1],
                'avg_blocks': stats['avg_blocks'],
                'avg_forks': stats['avg_forks'],
            })

        all_p95s[num_plays] = p95s
        all_detect_probs[num_plays] = detect_probs

    combined_csv = os.path.join(data_dir, 'sweep_results.csv')
    pd.DataFrame(all_rows).to_csv(combined_csv, index=False)

    raw_csv = os.path.join(data_dir, 'sweep_raw.csv')
    pd.concat(all_raw, ignore_index=True).to_csv(raw_csv, index=False)

    print(f"\nSummary saved to:  {combined_csv}")
    print(f"Raw data saved to: {raw_csv}")
    print(f"Nash eq files:     {nash_dir}/")

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))

    for strategy in strategies:
        num_plays = strategy['num_plays']
        ax1.plot(difficulties, all_p95s[num_plays],
                 marker=markers[num_plays], linestyle='-', color=colors[num_plays],
                 label=f'$c={num_plays}$', linewidth=1.5, markersize=6)

    mean_detect = np.mean([all_detect_probs[s['num_plays']] for s in strategies], axis=0)
    ax2.plot(difficulties, mean_detect,
             marker='o', linestyle='-', color='C0', linewidth=1.5, markersize=6)

    for ax in (ax1, ax2):
        ax.set_xscale('log', base=2)
        ax.xaxis.set_major_formatter(x_formatter)
        ax.set_xlabel(r'$D$', fontsize=13)
        ax.grid(True, alpha=0.3)

    ax1.set_ylabel(r'$P_{95}$', fontsize=13)
    ax2.set_ylabel(r'$P_{\mathrm{det}}$', fontsize=13)
    ax1.legend(fontsize=10)
    ax1.text(0.5, -0.18, r'(a)', fontsize=11, ha='center', va='top', transform=ax1.transAxes)
    ax2.text(0.5, -0.18, r'(b)', fontsize=11, ha='center', va='top', transform=ax2.transAxes)

    plt.tight_layout()
    plot_path = os.path.join(images_dir, 'sweep_p95_pdet_vs_difficulty.pdf')
    plt.savefig(plot_path, dpi=300, bbox_inches='tight')
    plt.show()

    print(f"\n{'='*60}")
    print("All simulations complete!")
    print(f"{'='*60}")

