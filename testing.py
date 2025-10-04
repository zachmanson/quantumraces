import numpy as np
import matplotlib.pyplot as plt

def generate_classical_timestamps(num_blocks, mean_time_sec, seed=42):
    np.random.seed(seed)
    inter_arrival = np.random.exponential(scale=mean_time_sec, size=num_blocks)
    timestamps = np.cumsum(inter_arrival)
    return timestamps

def valid_next_timestamp(prev_timestamps, candidate, classical_timestamp):
    """
    Returns True if candidate timestamp satisfies Bitcoin rules:
    1. Greater than median of previous 11 timestamps.
    2. Not more than 2 hours ahead of the classical network timestamp.
    """
    window = prev_timestamps[-11:] if len(prev_timestamps) >= 11 else prev_timestamps
    med = np.median(window)
    max_allowed = classical_timestamp + 2 * 3600  # 2 hours in seconds
    return candidate > med and candidate <= max_allowed

def generate_quantum_timestamps(num_blocks, classical_timestamps, classical_mean_time_sec, compression_factor):
    compressed_inter_block = classical_mean_time_sec / compression_factor
    quantum_timestamps = [0]  # start at zero for simplicity

    for i in range(1, num_blocks):
        candidate = quantum_timestamps[-1] + compressed_inter_block

        # Check Bitcoin rules
        window = quantum_timestamps[-11:] if len(quantum_timestamps) >= 11 else quantum_timestamps
        med = np.median(window)
        max_allowed = classical_timestamps[i] + 2*3600

        if candidate <= med:
            # Cannot compress below the median-of-11 rule
            raise ValueError(
                f"Impossible compression at block {i}: candidate {candidate:.1f}s "
                f"<= median of previous 11 ({med:.1f}s)."
            )
        if candidate > max_allowed:
            # Cannot go beyond 2 hours of classical network time
            raise ValueError(
                f"Impossible compression at block {i}: candidate {candidate:.1f}s "
                f"> 2 hours beyond classical timestamp ({max_allowed:.1f}s)."
            )

        quantum_timestamps.append(candidate)

    return np.array(quantum_timestamps)

def main():
    num_blocks = 1000
    mean_time_minutes = 10
    mean_time_sec = mean_time_minutes * 60

    # Generate classical timestamps
    classical_timestamps = generate_classical_timestamps(num_blocks, mean_time_sec)

    # Set compression factor (try large values like 64, 100, 1000)
    compression_factor = 400000

    try:
        quantum_timestamps = generate_quantum_timestamps(
            num_blocks, classical_timestamps, mean_time_sec, compression_factor
        )
    except ValueError as e:
        print(f"Compression factor {compression_factor} failed: {e}")
        return

    # Print stats
    classical_duration = classical_timestamps[-1] - classical_timestamps[0]
    quantum_duration = quantum_timestamps[-1] - quantum_timestamps[0]
    print(f"Classical chain duration (sec): {classical_duration:.1f} (~{classical_duration/3600:.2f} hours)")
    print(f"Quantum chain duration (sec): {quantum_duration:.1f} (~{quantum_duration/3600:.2f} hours)")
    print(f"Compression factor achieved: {classical_duration / quantum_duration:.2f}")

    # Plot
    plt.figure(figsize=(12,6))
    plt.plot(classical_timestamps / 3600, label='Classical chain timestamps (hours)')
    plt.plot(quantum_timestamps / 3600, label=f'Quantum compressed timestamps (factor {compression_factor})')
    plt.xlabel('Block height')
    plt.ylabel('Timestamp (hours)')
    plt.title('Classical vs Quantum Block Timestamps with Bitcoin Rules')
    plt.legend()
    plt.grid(True)
    plt.show()

if __name__ == "__main__":
    main()
