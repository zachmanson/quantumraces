import numpy as np


block_times = []
current_time = 0.0
simulation_time = 86400.0
while current_time < simulation_time:
    block_arrival_time = np.random.exponential(600.0)
    current_time += block_arrival_time

    if current_time < simulation_time:
        block_times.append(current_time)

print(block_times)
print(np.average([y - x for x, y in zip(block_times, block_times[1:])]))
