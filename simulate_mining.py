import analyze_NE as ane
import numpy as np
import random

class QuantumMiningSimulation:
    def __init__(self,
                nash_equilibrium: dict[str, list[tuple[list[float], float]]],
                num_simulations: int = 1000000,
                classical_block_rate: float = 1/600, #blocks per second: 1 every ~ 10 minutes 
                quantum_simulation_time: float = 86400.0, #one day in seconds
                difficulty: float =  82047028459932.62, #current network difficulty
                ) -> None:
        
        self.nash_eq = nash_equilibrium
        self.num_simulations = num_simulations
        self.classical_block_rate = classical_block_rate
        self.quantum_simulation_time = quantum_simulation_time #time over which to do the simulation by default this is one day 
        self.difficulty = difficulty

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
    
    def generate_quantum_measurement_times(self, strategy: list[float]) -> list[float]:
        optimal_iterations = np.floor(np.pi / 4 * np.sqrt(self.difficulty))
        time_per_iteration = 600 / optimal_iterations
        measurement_times: list[float] = []
        current_time = 0.0

        for iterations in strategy:
            time_for_iterations = iterations * time_per_iteration
            current_time += time_for_iterations
            measurement_times.append(current_time)

        return measurement_times
    
    def generate_classical_block_times(self) -> list[float]:
        block_times: list[float] = []
        current_time = 0.0

        while current_time < self.quantum_simulation_time:
            block_arrival_time = np.random.exponential(1/self.classical_block_rate)
            current_time += block_arrival_time

            if current_time < self.quantum_simulation_time:
                block_times.append(current_time)

        return block_times

    def simulate_single_run():
        pass

    def simulate():
        pass
