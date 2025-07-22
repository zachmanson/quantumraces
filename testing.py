import re
import numpy as np

def parse_and_sum_probabilities(text):
    blocks = text.strip().split("-------------")
    results = []

    for block_num, block in enumerate(blocks):
        alice_sum = 0.0
        bob_sum = 0.0
        lines = block.strip().split("\n")
        
        for line in lines:
            match = re.match(r"(Alice|Bob)\s+\[.*?\]\s+([0-9\.eE+-]+)", line)
            if match:
                name = match.group(1)
                prob = float(match.group(2))
                if name == "Alice":
                    alice_sum += prob
                elif name == "Bob":
                    bob_sum += prob

        results.append((block_num + 1, alice_sum, bob_sum))

    return results

# Example usage
if __name__ == "__main__":
    # Replace this with reading from a file if needed
    with open("output.txt", "r") as f:
        input_text = f.read()

    results = parse_and_sum_probabilities(input_text)
    
    for i, alice_total, bob_total in results:
        print(f"Block {i}:")
        print(f"  Alice total probability: {alice_total:.10f}")
        print(f"  Bob total probability:   {bob_total:.10f}")
        print()
