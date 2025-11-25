import numpy as np
from buildpayoff import BuildPayoff
import math

def parse_nash_eq_from_file(filename: str) -> (dict, dict): 
    alice_strats: dict = {}
    bob_strats: dict = {}
    with open(filename, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line == '-------------':
                continue
            parts = line.split()
            player = parts[0]
            strat_start = line.index('[')
            strat_end = line.index(']')
            strat_str = line[strat_start+1:strat_end]
            strat_values: list = []
            for val_str in strat_str.split(','):
                val_str = val_str.strip()
                if 'np.int64(' in val_str:
                    val = int(val_str.split('(')[1].split(')')[0])
                else:
                    val = int(val_str)
                strat_values.append(val)
            prob = float(parts[-1])
            strat_tuple = tuple(strat_values)
            if player == "Alice":
                alice_strats[strat_tuple] = prob
            else:
                bob_strats[strat_tuple] = prob
    return alice_strats, bob_strats

def format_sig(x: float, sig: int = 4) -> str:
    if x == 0:
        return "0." + "0"*(sig-1)
    decimals = sig - int(math.floor(math.log10(abs(x)))) - 1
    return f"{x:.{decimals}f}"

def main() -> None:
    alice_mixed, bob_mixed = parse_nash_eq_from_file('output.txt')
    print(f"Alice has {len(alice_mixed)} strategies in support")
    print(f"Bob has {len(bob_mixed)} strategies in support")
    all_iterations: list = []
    for strat in alice_mixed.keys():
        all_iterations.extend(strat)
    for strat in bob_mixed.keys():
        all_iterations.extend(strat)
    max_iterations = max(all_iterations)
    num_plays = len(list(alice_mixed.keys())[0])
    print(f"Max iterations: {max_iterations}")
    print(f"Number of plays: {num_plays}")
    D = 119116256505723.5 # difficulty as of May 9 2025
    #D = 3651011.631 # difficulty as of Feb 26 2013
    gamma = 0.5
    builder = BuildPayoff(
        K=max_iterations, 
        num_plays=num_plays, 
        D=D, 
        clustering_factor=1.0,  
        gamma=gamma,
        scale_with_D = False
    )
    alice_expected = builder.compute_expected_payoff(alice_mixed, bob_mixed, player="Alice")
    bob_expected = builder.compute_expected_payoff(alice_mixed, bob_mixed, player="Bob")
    print(f"\nExpected payoff for Alice: {repr(alice_expected)}")
    print(f"Expected payoff for Bob: {repr(bob_expected)}")

if __name__ == "__main__":
    main()
