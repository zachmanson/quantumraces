import numpy as np
import math
import matplotlib.pyplot as plt
import pandas as pd
from typing import List, Tuple

class QuantumMiningSimulatorFixed:
    def __init__(self,
                 c: float,  # Number of measurement attempts per block
                 num_simulations: int = 10000,
                 classical_block_rate: float = 1/600,  # blocks per second: 1 every 10 minutes
                 quantum_simulation_time: float = 86400.0,  # seconds in a day
                 difficulty: float = 119116256505723.5,  # current difficulty
                 fixed_iterations: int = 51471  # Fixed Grover iterations
    ) -> None:
        self.c = int(c)  # Convert to int for faster operations
        self.num_simulations = num_simulations
        self.classical_block_rate = classical_block_rate
        self.quantum_simulation_time = quantum_simulation_time
        self.difficulty = difficulty
        self.fixed_iterations = fixed_iterations
        
        # Time per individual measurement (600 seconds total divided by c measurements)
        self.time_per_measurement = 600.0 / c
        # Time per Grover iteration within each measurement
        self.seconds_per_iteration = self.time_per_measurement / fixed_iterations
        
        # Pre-calculate probabilities to avoid repeated computation
        self.theta = math.asin(1 / math.sqrt(difficulty))
        self.success_probability = (math.sin((2 * fixed_iterations + 1) * self.theta))**2
        
        # Pre-calculate AQMS probabilities for common iteration counts
        self.max_aqms_iterations = fixed_iterations
        self.aqms_probs = np.zeros(self.max_aqms_iterations + 1)
        for i in range(1, self.max_aqms_iterations + 1):
            self.aqms_probs[i] = (math.sin((2 * i + 1) * self.theta))**2

    def time_to_iterations_completed(self, elapsed_time: float) -> int:
        """Calculate how many iterations completed given elapsed time"""
        return min(int(elapsed_time / self.seconds_per_iteration), self.fixed_iterations)
    
    def aggressive_measurement_probability(self, iterations_completed: int) -> float:
        """Get pre-calculated success probability for AQMS with partial iterations"""
        if iterations_completed <= 0 or iterations_completed >= len(self.aqms_probs):
            return 0.0
        return self.aqms_probs[iterations_completed]

    def simulate_vectorized(self) -> Tuple[float, int, int, int]:
        """Vectorized simulation using numpy arrays"""
        
        # Generate all random numbers needed upfront - much larger buffer for high c values
        max_events_estimate = max(500, self.c * 50)  # Scale with c since more measurements = more events
        random_vals = np.random.random(max_events_estimate * self.num_simulations)
        random_idx = 0
        
        # Results arrays
        all_stale_rates = np.zeros(self.num_simulations)
        all_blocks = np.zeros(self.num_simulations, dtype=int)
        all_forks = np.zeros(self.num_simulations, dtype=int) 
        all_quantum_blocks = np.zeros(self.num_simulations, dtype=int)
        
        for sim in range(self.num_simulations):
            current_time = 0.0
            total_blocks = 0
            total_forks = 0
            total_quantum_blocks = 0
            
            # Generate all classical block times for this simulation
            expected_classical_blocks = int(self.quantum_simulation_time * self.classical_block_rate) + 10
            classical_intervals = np.random.exponential(1/self.classical_block_rate, expected_classical_blocks)
            classical_times = np.cumsum(classical_intervals)
            classical_times = classical_times[classical_times < self.quantum_simulation_time]
            classical_idx = 0
            
            while current_time < self.quantum_simulation_time and classical_idx < len(classical_times):
                # Generate quantum measurement times for this cycle
                alice_times = current_time + np.arange(1, self.c + 1) * self.time_per_measurement
                bob_times = current_time + np.arange(1, self.c + 1) * self.time_per_measurement
                
                # Find all events in this cycle
                alice_active = alice_times < self.quantum_simulation_time
                bob_active = bob_times < self.quantum_simulation_time
                
                alice_times = alice_times[alice_active]
                bob_times = bob_times[bob_active]
                
                # Combine all event times
                all_event_times = []
                event_types = []
                
                for i, t in enumerate(alice_times):
                    all_event_times.append(t)
                    event_types.append(('alice', i))
                    
                for i, t in enumerate(bob_times):
                    all_event_times.append(t)
                    event_types.append(('bob', i))
                
                # Add next classical block if within range
                if classical_idx < len(classical_times):
                    all_event_times.append(classical_times[classical_idx])
                    event_types.append(('classical', classical_idx))
                
                if not all_event_times:
                    break
                    
                # Sort events by time
                event_order = np.argsort(all_event_times)
                
                alice_attempts_made = 0
                bob_attempts_made = 0
                cycle_start_time = current_time
                
                # Process events in chronological order
                for event_idx in event_order:
                    event_time = all_event_times[event_idx]
                    event_type, event_data = event_types[event_idx]
                    
                    if event_time >= self.quantum_simulation_time:
                        break
                        
                    current_time = event_time
                    
                    if event_type == 'alice':
                        # Alice measurement
                        if random_idx >= len(random_vals):
                            # Generate more random numbers if needed
                            random_vals = np.random.random(len(random_vals))
                            random_idx = 0
                            
                        if random_vals[random_idx] <= self.success_probability:
                            # Alice succeeds
                            total_blocks += 1
                            total_quantum_blocks += 1
                            random_idx += 1
                            
                            # Bob AQMS if active
                            if bob_attempts_made < self.c:
                                elapsed = current_time - cycle_start_time - (bob_attempts_made * self.time_per_measurement)
                                if elapsed > 0:
                                    iterations = self.time_to_iterations_completed(elapsed)
                                    if iterations > 0:
                                        if random_idx >= len(random_vals):
                                            random_vals = np.random.random(len(random_vals))
                                            random_idx = 0
                                        aqms_prob = self.aggressive_measurement_probability(iterations)
                                        if random_vals[random_idx] <= aqms_prob:
                                            total_blocks += 1
                                            total_quantum_blocks += 1
                                            total_forks += 1
                                        random_idx += 1
                            
                            # End cycle - generate new classical times
                            classical_intervals = np.random.exponential(1/self.classical_block_rate, expected_classical_blocks)
                            new_classical_times = current_time + np.cumsum(classical_intervals)
                            classical_times = new_classical_times[new_classical_times < self.quantum_simulation_time]
                            classical_idx = 0
                            break
                        else:
                            alice_attempts_made += 1
                            random_idx += 1
                            
                    elif event_type == 'bob':
                        # Bob measurement
                        if random_idx >= len(random_vals):
                            random_vals = np.random.random(len(random_vals))
                            random_idx = 0
                            
                        if random_vals[random_idx] <= self.success_probability:
                            # Bob succeeds
                            total_blocks += 1
                            total_quantum_blocks += 1
                            random_idx += 1
                            
                            # Alice AQMS if active
                            if alice_attempts_made < self.c:
                                elapsed = current_time - cycle_start_time - (alice_attempts_made * self.time_per_measurement)
                                if elapsed > 0:
                                    iterations = self.time_to_iterations_completed(elapsed)
                                    if iterations > 0:
                                        if random_idx >= len(random_vals):
                                            random_vals = np.random.random(len(random_vals))
                                            random_idx = 0
                                        aqms_prob = self.aggressive_measurement_probability(iterations)
                                        if random_vals[random_idx] <= aqms_prob:
                                            total_blocks += 1
                                            total_quantum_blocks += 1
                                            total_forks += 1
                                        random_idx += 1
                            
                            # End cycle - generate new classical times
                            classical_intervals = np.random.exponential(1/self.classical_block_rate, expected_classical_blocks)
                            new_classical_times = current_time + np.cumsum(classical_intervals)
                            classical_times = new_classical_times[new_classical_times < self.quantum_simulation_time]
                            classical_idx = 0
                            break
                        else:
                            bob_attempts_made += 1
                            random_idx += 1
                            
                    elif event_type == 'classical':
                        # Classical block found
                        total_blocks += 1
                        classical_idx += 1
                        
                        # Both miners try AQMS
                        if alice_attempts_made < self.c:
                            elapsed = current_time - cycle_start_time - (alice_attempts_made * self.time_per_measurement)
                            if elapsed > 0:
                                iterations = self.time_to_iterations_completed(elapsed)
                                if iterations > 0:
                                    if random_idx >= len(random_vals):
                                        random_vals = np.random.random(len(random_vals))
                                        random_idx = 0
                                    aqms_prob = self.aggressive_measurement_probability(iterations)
                                    if random_vals[random_idx] <= aqms_prob:
                                        total_blocks += 1
                                        total_quantum_blocks += 1
                                        total_forks += 1
                                    random_idx += 1
                        
                        if bob_attempts_made < self.c:
                            elapsed = current_time - cycle_start_time - (bob_attempts_made * self.time_per_measurement)
                            if elapsed > 0:
                                iterations = self.time_to_iterations_completed(elapsed)
                                if iterations > 0:
                                    if random_idx >= len(random_vals):
                                        random_vals = np.random.random(len(random_vals))
                                        random_idx = 0
                                    aqms_prob = self.aggressive_measurement_probability(iterations)
                                    if random_vals[random_idx] <= aqms_prob:
                                        total_blocks += 1
                                        total_quantum_blocks += 1
                                        total_forks += 1
                                    random_idx += 1
                        
                        # End cycle
                        break
                else:
                    # All quantum attempts exhausted, wait for next classical block
                    if classical_idx < len(classical_times):
                        current_time = classical_times[classical_idx]
                        if current_time < self.quantum_simulation_time:
                            total_blocks += 1
                            classical_idx += 1

            all_stale_rates[sim] = total_forks / total_blocks if total_blocks > 0 else 0
            all_blocks[sim] = total_blocks
            all_forks[sim] = total_forks
            all_quantum_blocks[sim] = total_quantum_blocks
            
            # Reset random index if running low
            if random_idx > len(random_vals) - 100:  # Leave more buffer
                random_vals = np.random.random(max_events_estimate * self.num_simulations)
                random_idx = 0
        
        return np.mean(all_stale_rates), np.mean(all_blocks), np.mean(all_forks), np.mean(all_quantum_blocks)

    def simulate_all(self) -> dict:
        """Run all simulations and return averaged results"""
        print(f'Running {self.num_simulations} simulations for c = {self.c}...')
        
        avg_stale_rate, avg_blocks, avg_forks, avg_quantum_blocks = self.simulate_vectorized()
        
        # Calculate derived metrics
        threshold_51 = (1 - avg_stale_rate) / (2 - avg_stale_rate) if avg_stale_rate < 1 else 0
        quantum_percentage = (avg_quantum_blocks / avg_blocks * 100) if avg_blocks > 0 else 0

        return {
            'c': self.c,
            'stale_rate': avg_stale_rate,
            'threshold_51': threshold_51,
            'blocks_per_day': avg_blocks,
            'forks_per_day': avg_forks,
            'quantum_blocks_per_day': avg_quantum_blocks,
            'quantum_percentage': quantum_percentage
        }


def simulate_across_c_values(c_values: List[float], num_simulations: int = 10000) -> pd.DataFrame:
    """Simulate across different c values and return results DataFrame"""
    results = []
    
    for c in c_values:
        print(f'\n{"="*50}')
        print(f'Starting c = {c}')
        print(f'{"="*50}')
        
        import time
        start_time = time.time()
        
        simulator = QuantumMiningSimulatorFixed(c=c, num_simulations=num_simulations)
        result = simulator.simulate_all()
        
        end_time = time.time()
        elapsed = end_time - start_time
        print(f'Completed c = {c} in {elapsed:.1f} seconds')
        
        results.append(result)
        
        print(f'Results for c = {c}:')
        print(f'  Stale Rate: {result["stale_rate"]:.6f}')
        print(f'  51% Threshold: {result["threshold_51"]:.6f}')
        print(f'  Blocks/day: {result["blocks_per_day"]:.2f}')
        print(f'  Quantum %: {result["quantum_percentage"]:.2f}%')
    
    return pd.DataFrame(results)


def create_plots_and_save_data(results_df: pd.DataFrame):
    """Create individual plots for each metric and save data to CSV files"""
    
    # Create plots
    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    axes = axes.flatten()
    
    metrics = [
        ('stale_rate', 'Stale Rate', 'stale_rate_data.csv'),
        ('threshold_51', '51% Attack Threshold', 'threshold_51_data.csv'), 
        ('blocks_per_day', 'Blocks Found Per Day', 'blocks_per_day_data.csv'),
        ('forks_per_day', 'Forks Found Per Day', 'forks_per_day_data.csv'),
        ('quantum_blocks_per_day', 'Quantum Blocks Per Day', 'quantum_blocks_data.csv'),
        ('quantum_percentage', '% Blocks Found by Quantum Miners', 'quantum_percentage_data.csv')
    ]
    
    for i, (metric, title, csv_name) in enumerate(metrics):
        # Create individual plot
        plt.figure(figsize=(10, 6))
        plt.loglog(results_df['c'], results_df[metric], 'o-', linewidth=2, markersize=8)
        plt.xlabel('c (Number of Measurements per Block)', fontsize=12)
        plt.ylabel(title, fontsize=12)
        plt.title(f'{title} vs c', fontsize=14)
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(f'images/{metric}_vs_c.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # Add to subplot
        axes[i].loglog(results_df['c'], results_df[metric], 'o-', linewidth=2, markersize=6)
        axes[i].set_xlabel('c')
        axes[i].set_ylabel(title)
        axes[i].set_title(title)
        axes[i].grid(True, alpha=0.3)
        
        # Save individual CSV
        metric_df = results_df[['c', metric]].copy()
        metric_df.to_csv(csv_name, index=False)
        print(f'Saved {csv_name}')
    
    plt.tight_layout()
    plt.savefig('images/all_metrics_vs_c.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    # Save complete results
    results_df.to_csv('complete_simulation_results.csv', index=False)
    print('Saved complete_simulation_results.csv')


def main():
    c_values = [1.0, 2.0, 5.0, 10.0, 25.0, 50.0, 100.0, 250.0, 500.0, 1000.0, 2500.0, 5000.0, 10000.0, 25000.0]
    
    num_simulations = 1000
    
    print("Starting Quantum Mining Simulation with Fixed Iterations")
    print(f"Fixed iterations per measurement: 51471")
    print(f"Number of simulations per c value: {num_simulations}")
    print(f"c values: {c_values}")
    
    results_df = simulate_across_c_values(c_values, num_simulations)
    
    print("\n" + "="*80)
    print("SIMULATION RESULTS SUMMARY")
    print("="*80)
    print(results_df.to_string(index=False, float_format='%.6f'))
    print("="*80)
    
    if len(c_values) > 1:
        create_plots_and_save_data(results_df)
    
    print("\nSimulation complete!")


if __name__ == '__main__':
    main()