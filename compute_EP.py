import numpy as np
from buildpayoff import BuildPayoff  # or whatever your file is named

def parse_nash_eq_from_file(filename: str):
    alice_strats = {}
    bob_strats = {}
    
    with open(filename, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line == '-------------':
                continue
            
            parts = line.split()
            player = parts[0]  # Alice or Bob
            
            strat_start = line.index('[')
            strat_end = line.index(']')
            strat_str = line[strat_start+1:strat_end]
            
            strat_values = []
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

def main():
    alice_mixed, bob_mixed = parse_nash_eq_from_file('output.txt')
    
    print(f"Alice has {len(alice_mixed)} strategies in support")
    print(f"Bob has {len(bob_mixed)} strategies in support")
    
    all_iterations = []
    for strat in alice_mixed.keys():
        all_iterations.extend(strat)
    for strat in bob_mixed.keys():
        all_iterations.extend(strat)
    
    max_iterations = max(all_iterations)
    num_plays = len(list(alice_mixed.keys())[0])  
    
    print(f"Max iterations: {max_iterations}")
    print(f"Number of plays: {num_plays}")
    
    #D = 119116256505723.5 #difficulty as of May 9 2025
    D = 3651011.631 #difficulty as of Feb 26 2013
    gamma = 0.5
    
    builder = BuildPayoff(
        K=max_iterations, 
        num_plays=num_plays, 
        D=D, 
        clustering_factor=1.0,  
        gamma=gamma,
        scale_with_D=False  
    )
    
    alice_expected = builder.compute_expected_payoff(alice_mixed, bob_mixed, player="Alice")
    bob_expected = builder.compute_expected_payoff(alice_mixed, bob_mixed, player="Bob")

    print(f"\nExpected payoff for Alice: {alice_expected:.4f}")
    print(f"Expected payoff for Bob: {bob_expected:.4f}")

if __name__ == "__main__":
    main()