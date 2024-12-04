import analyze_NE as ane
import numpy as np
import random
import twoplayer as tp

class QuantumMiningSimulation:
    def __init__(self,
                nash_equilibrium: dict[str, list[tuple[list[float], float]]],
                num_simulations: int = 1000000,
                classical_block_rate: float = 1/600,
                quantum_simulation_time: float = 86400.0) -> None:
        
        self.nash_eq = nash_equilibrium
        self.num_simulations = num_simulations
        self.classical_block_rate = classical_block_rate
        self.quantum_simulation_time = quantum_simulation_time #time over which to do the simulation by default this is one day 

    def select_strategy(self) -> tuple:
        alice_strats = self.nash_eq['Alice']
        bob_strats = self.nash_eq['Bob']

        alice_strategy = random.choices(
            [strat[0] for strat in alice_strats],
            weights = [strat[1] for strat in alice_strats]
        )[0]

        bob_strategy = random.choices(
            [strat[0] for strat in bob_strats],
            weights = [strat[1] for strat in bob_strats]
        )[0]

        return (alice_strategy, bob_strategy)
    
    def generate_classical_block_times(self) -> list[float]:
        block_times: list[float] = []
        current_time: float = 0

        while current_time < self.quantum_simulation_time:
            block_arrival_time = np.random.exponential(1/self.classical_block_rate)
            current_time += block_arrival_time

            if current_time < self.quantum_simulation_time:
                block_times.append(current_time)

        return block_times
    
    def generate_quantum_measurement_times(self, strategy: list[float], time_per_iteration: float = 0.001) -> list[float]:
        return


    def simulate_single_run(self, quantum_strategy: tuple[list[float], list[float]]) -> tuple[int, int]:

        alice_strat, bob_strat = quantum_strategy
        num_blocks = 0
        num_forks = 0

        classical_block_times = self.generate_classical_block_times()
        
        alice_measurement_times = self.generate_quantum_measurement_times(alice_strat)

        return 

    def simulate(self) -> float:

        total_forks = 0
        total_blocks = 0

        for _ in range(self.num_simulations):
            quantum_strategy = self.select_strategy()
            num_blocks, num_forks = self.simulate_single_run(quantum_strategy)

            total_blocks += num_blocks
            total_forks += num_forks

        return total_forks / total_blocks if total_blocks > 0 else 0


