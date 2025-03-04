from analyze_nasheqs import NashEquilibriaAnalyzer
import numpy as np
import random
import math

class QuantumMiningSimulation:
    def __init__(self,
                nash_equilibrium: dict[str, list[tuple[list[float], float]]],
                intvl: int, #the number of iterations per interval
                num_simulations: int = 10000,
                classical_block_rate: float = 1/600, #blocks per second: 1 every ~ 10 minutes 
                quantum_simulation_time: float = 86400.0, #one day in seconds
                difficulty: float =  82047028459932.62 #current network difficulty
                ) -> None:
        
        self.nash_eq = nash_equilibrium
        self.intvl = intvl  
        self.num_simulations = num_simulations
        self.classical_block_rate = classical_block_rate
        self.quantum_simulation_time = quantum_simulation_time #time over which to do the simulation by default this is one day 
        self.difficulty = difficulty

    def measurement_probability(self, iterations: int) -> float:
        return (math.sin(2 * (iterations + 1/2) * math.asin(1/np.sqrt(self.difficulty)))**2)

    def select_strategy(self) -> tuple[list[float], list[float]]:
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
    
    def time_to_iterations(self, time: float) -> int: 
        optimal_iterations = np.floor(np.pi / 4 * np.sqrt(self.difficulty))
        time_per_iteration = 600 / optimal_iterations

        return time // time_per_iteration
    
    def iterations_to_time(self, iterations: int) -> float:
        optimal_iterations = np.floor(np.pi / 4 * np.sqrt(self.difficulty))
        time_per_iteration = 600 / optimal_iterations

        return iterations * time_per_iteration

    def generate_quantum_measurement_times(self, strategy: list[float], current_time: float = 0.0) -> list[float]:
        optimal_iterations = np.floor(np.pi / 4 * np.sqrt(self.difficulty))
        time_per_iteration = 600 / optimal_iterations
        measurement_times: list[float] = []
        
        for iterations in strategy:
            time_for_iterations = iterations * time_per_iteration
            current_time += time_for_iterations
            if current_time <= self.quantum_simulation_time:
                measurement_times.append(current_time)
            else:
                break
    
        return measurement_times
    
    def generate_classical_block_times(self, current_time = 0.0) -> list[float]:
        block_times: list[float] = []

        while current_time < self.quantum_simulation_time:
            block_arrival_time = np.random.exponential(1/self.classical_block_rate)
            current_time += block_arrival_time

            if current_time < self.quantum_simulation_time:
                block_times.append(current_time)
            else:
                break

        return block_times
    
    def simulate_single_run(
        self,
        quantum_strategy: tuple[list[float], list[float]],
        classical_block_times: list[float],
        initial_classical_index: int,
        initial_current_time: float
    ) -> tuple[int, int, float, int, list[float]]:

        # returns the number of blocks added, number of forks, total time elapsed, and the new classical index
        alice_strat, bob_strat = quantum_strategy
        alice_measurement_times = self.generate_quantum_measurement_times(alice_strat, initial_current_time)
        bob_measurement_times = self.generate_quantum_measurement_times(bob_strat, initial_current_time)

        num_blocks = 0
        num_forks = 0

        classical_index = initial_classical_index
        alice_index = 0
        bob_index = 0

        last_alice_measured_time = initial_current_time
        last_bob_measured_time = initial_current_time

        current_time = initial_current_time  # track the total time of the simulation

        optimal_iterations = np.floor(np.pi / 4 * np.sqrt(self.difficulty))

        # Simulate until we have used up all of our measurement and block times.
        while alice_index < len(alice_measurement_times) or bob_index < len(bob_measurement_times) or classical_index < len(
                classical_block_times):
            # determine when is the next event
            events = [
                (alice_measurement_times[alice_index] if alice_index < len(alice_measurement_times) else float('inf'),
                'Alice'),  # get next alice block time
                (bob_measurement_times[bob_index] if bob_index < len(bob_measurement_times) else float('inf'),
                'Bob'),  # get next bob block time
                (classical_block_times[classical_index] if classical_index < len(classical_block_times) else float('inf'),
                'Classical')  # get next classical block time
            ]

            # sort by the time
            events.sort(key=lambda x: x[0])

            next_event_time, event_type = events[0]

            if next_event_time > self.quantum_simulation_time:
                return num_blocks, num_forks, current_time, classical_index, classical_block_times

            current_time = next_event_time  # Advance current time *always*

            if event_type == 'Classical':
                num_blocks += 1

                # Alice and Bob Measure Independently (regardless of success, the time has passed)
                r_alice = random.random()
                alice_aggressive_iterations = self.time_to_iterations(
                    current_time - last_alice_measured_time)  if last_alice_measured_time > 0 else 0
                if r_alice <= self.measurement_probability(alice_aggressive_iterations):
                    num_forks += 1

                r_bob = random.random()
                bob_aggressive_iterations = self.time_to_iterations(
                    current_time - last_bob_measured_time)  if last_bob_measured_time > 0 else 0
                if r_bob <= self.measurement_probability(bob_aggressive_iterations):
                    num_forks += 1

                # set the last measured times to current time
                last_alice_measured_time = current_time
                last_bob_measured_time = current_time

                classical_index += 1  # increment classical index

                # Since this is a classical block, return right away
                return num_blocks, num_forks, current_time, classical_index, classical_block_times

            elif event_type == 'Alice':  # alice is making a measurement
                r_alice = random.random()
                alice_iterations = alice_strat[alice_index]
                last_alice_measured_time = current_time  # Update Alice's last measurement time (always, strategical time)

                # check if this measurement was successful, if so, then create a new block and calculate forks.
                if r_alice <= self.measurement_probability(int(alice_iterations)):
                    num_blocks += 1

                    # if Alice has a successful measurement, Bob may also try to fork. Check the time difference.
                    r_bob = random.random()
                    bob_aggressive_iterations = self.time_to_iterations(
                        current_time - last_bob_measured_time) if last_bob_measured_time > 0 else 0
                    if r_bob <= self.measurement_probability(bob_aggressive_iterations):
                        num_forks += 1

                    last_bob_measured_time = current_time  # also set bob to current

                    # Since there is a quantum block, return the new set and also reset the index
                    classical_block_times = self.generate_classical_block_times(current_time=current_time)
                    alice_measurement_times = self.generate_quantum_measurement_times(alice_strat,
                                                                                        current_time)  # regen times
                    bob_measurement_times = self.generate_quantum_measurement_times(bob_strat,
                                                                                    current_time)
                    alice_index = 0
                    bob_index = 0
                    return num_blocks, num_forks, current_time, 0, classical_block_times  # reset classical index

                alice_index += 1  # move to the next measurement for alice

            elif event_type == 'Bob':  # bob is making a measurement
                r_bob = random.random()
                bob_iterations = bob_strat[bob_index]
                last_bob_measured_time = current_time  # Update Bob's last measurement time (always, strategical time)

                # check if this measurement was successful, if so, then create a new block and calculate forks.
                if r_bob <= self.measurement_probability(int(bob_iterations)):
                    num_blocks += 1

                    # check for forks here, also use that last_alice_measured is 0 if it is the first block
                    r_alice = random.random()
                    alice_aggressive_iterations = self.time_to_iterations(
                        current_time - last_alice_measured_time) if last_alice_measured_time > 0 else 0
                    if r_alice <= self.measurement_probability(alice_aggressive_iterations):
                        num_forks += 1

                    last_alice_measured_time = current_time

                    # Since there is a quantum block, return the new times and index
                    classical_block_times = self.generate_classical_block_times(current_time=current_time)
                    alice_measurement_times = self.generate_quantum_measurement_times(alice_strat,
                                                                                        current_time)  # regen times
                    bob_measurement_times = self.generate_quantum_measurement_times(bob_strat,
                                                                                    current_time)
                    alice_index = 0
                    bob_index = 0
                    return num_blocks, num_forks, current_time, 0, classical_block_times  # reset classical index

                bob_index += 1

        return num_blocks, num_forks, current_time, classical_index, classical_block_times


    def simulate(self) -> tuple[float, float, float]:
        #returns the average fork rate, the average block rate, and average simulation time

        total_forks = 0.0
        total_blocks = 0.0
        total_sim_time = 0.0

        classical_block_times = self.generate_classical_block_times()
        classical_index = 0
        current_time = 0.0

        while current_time < self.quantum_simulation_time:
            quantum_strategies = self.select_strategy()
            num_blocks, num_forks, sim_time, classical_index, classical_block_times = self.simulate_single_run(quantum_strategies, classical_block_times, classical_index, current_time)
            total_blocks += num_blocks
            total_forks += num_forks
            total_sim_time += sim_time

            if current_time + sim_time >= self.quantum_simulation_time:
                break

            current_time += sim_time

        avg_fork_rate = total_forks / total_blocks if total_blocks > 0 else 0 
        avg_block_rate = total_blocks / total_sim_time if total_sim_time > 0 else 0
        return avg_fork_rate, avg_block_rate, total_sim_time

    def simulate_all(self) -> tuple[float, float, float]:
        #returns the average fork rate, the average block rate (per second), and average simulation time

        total_forks = 0.0
        total_blocks = 0.0
        total_sim_time = 0.0

        for _ in range(self.num_simulations):
            avg_fork_rate, avg_block_rate, sim_time = self.simulate()

            total_forks += avg_fork_rate
            total_blocks += avg_block_rate
            total_sim_time += sim_time

        avg_fork_rate = total_forks / self.num_simulations
        avg_block_rate = total_blocks / self.num_simulations
        return avg_fork_rate, avg_block_rate, total_sim_time / self.num_simulations
    
def main():
    fname = 'output.txt'
    analyzer = NashEquilibriaAnalyzer()
    nash_eq = analyzer.converge(fname)
    simulator = QuantumMiningSimulation(nash_eq, intvl = analyzer.intvl, num_simulations = 1, difficulty = analyzer.D)

    avg_fork_rate, avg_block_rate, avg_sim_time = simulator.simulate_all()
    print('Average Fork Rate: ', avg_fork_rate)
    print('Average Block Rate: ', avg_block_rate)
    print('Average Simulation Time: ', avg_sim_time)

if __name__ == '__main__':
    main()