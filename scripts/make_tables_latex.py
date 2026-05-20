import re
import pandas as pd

def parse_strategy(strategy_str: str, normalize: bool = False, max_iterations: int = 1500) -> tuple:
    numbers = list(map(int, re.findall(r'np\.int64\((\d+)\)', strategy_str)))
    if normalize:
        return tuple(round(n / max_iterations, 2) for n in numbers)
    else:
        return tuple(numbers)

def determine_decimal_places(probabilities: list) -> int:
    min_decimal_places = 2
    max_decimal_places = 8
    
    for decimal_places in range(min_decimal_places, max_decimal_places + 1):
        rounded_probs = [round(p, decimal_places) for p in probabilities]
        
        all_distinguishable = True
        for i, orig_prob in enumerate(probabilities):
            rounded_prob = rounded_probs[i]
            
            if orig_prob > 0 and rounded_prob == 0:
                all_distinguishable = False
                break
            
            for j, other_prob in enumerate(probabilities):
                if i != j and abs(orig_prob - other_prob) > 0:
                    if round(orig_prob, decimal_places) == round(other_prob, decimal_places):
                        if abs(orig_prob - other_prob) > 10**(-decimal_places-1):
                            all_distinguishable = False
                            break
            
            if not all_distinguishable:
                break
        
        if all_distinguishable:
            return decimal_places
    
    return max_decimal_places

def process_file(input_file: str, output_file: str, normalize: bool = False, max_iterations: int = 1500) -> None:
    with open(input_file, 'r') as f:
        lines = f.readlines()

    blocks = []
    current_block = []

    for line in lines:
        line = line.strip()
        if line == "-------------":
            if current_block:
                blocks.append(current_block)
                current_block = []
        elif line:
            current_block.append(line)

    if current_block:
        blocks.append(current_block)

    with open(output_file, 'w') as f:
        f.write(r'\begin{tabular}{|c|c|c|}' + '\n')
        f.write(r'\hline' + '\n')
        f.write('Player & Pure Strategy & Probability \\\\ \n')
        f.write(r'\hline' + '\n')

        for i, block in enumerate(blocks):
            probabilities = []
            for entry in block:
                match = re.match(r'(Alice|Bob)\s+\[(.*?)\]\s+([\d\.eE+-]+)', entry)
                if match:
                    _, _, probability = match.groups()
                    probabilities.append(float(probability))
            
            decimal_places = determine_decimal_places(probabilities)
            
            for entry in block:
                match = re.match(r'(Alice|Bob)\s+\[(.*?)\]\s+([\d\.eE+-]+)', entry)
                if match:
                    player, strategy_str, probability = match.groups()
                    strategy = parse_strategy(strategy_str, normalize=normalize, max_iterations=max_iterations)
                    
                    if normalize:
                        strategy_latex = '(' + ', '.join(f"{x:.2f}" for x in strategy) + ')'
                    else:
                        strategy_latex = str(strategy)
                    
                    prob_formatted = f"{float(probability):.{decimal_places}f}"
                    
                    f.write(f'{player} & {strategy_latex} & {prob_formatted} \\\\ \n')
            
            if i < len(blocks) - 1:
                f.write(r'\hline\hline' + '\n')

        f.write(r'\hline' + '\n')
        f.write(r'\end{tabular}' + '\n')

def check_probability_sums(input_file: str) -> None:
    with open(input_file, 'r') as f:
        lines = f.readlines()

    blocks = []
    current_block = []

    for line in lines:
        line = line.strip()
        if line == "-------------":
            if current_block:
                blocks.append(current_block)
                current_block = []
        elif line:
            current_block.append(line)

    if current_block:
        blocks.append(current_block)

    for i, block in enumerate(blocks):
        sums = {'Alice': 0.0, 'Bob': 0.0}
        for line in block:
            match = re.match(r'(Alice|Bob)\s+\[.*?\]\s+([\d\.eE+-]+)', line)
            if match:
                player, prob = match.groups()
                sums[player] += float(prob)
        print(f"Equilibrium {i+1}: Alice = {sums['Alice']:.12f}, Bob = {sums['Bob']:.12f}")

def csv_to_latex_table(csv_file: str, output_file: str) -> None:
    df = pd.read_csv(csv_file)
    
    df = df[['difficulty', 'log2_difficulty', 'stale_rate']]
    
    stale_rates = df['stale_rate'].tolist()
    decimal_places = determine_decimal_places(stale_rates)
    
    with open(output_file, 'w') as f:
        f.write(r'\begin{tabular}{|c|c|c|}' + '\n')
        f.write(r'\hline' + '\n')
        f.write(r'$D$ & $\log_2(D)$ & $p_{\text{stale}}$ \\' + '\n')
        f.write(r'\hline' + '\n')
        
        for _, row in df.iterrows():
            difficulty = int(row['difficulty'])
            log2_diff = int(row['log2_difficulty'])
            stale_rate = row['stale_rate']
            
            f.write(f'{difficulty} & {log2_diff} & {stale_rate:.{decimal_places}f} \\\\ \n')
        
        f.write(r'\hline' + '\n')
        f.write(r'\end{tabular}' + '\n')

if __name__ == "__main__": 
    max_iterations = 8571866
    #max_iterations = 1500
    #process_file('output.txt', 'output_latex.tex', normalize=False, max_iterations=max_iterations)
    #check_probability_sums('output.txt')
    
    csv_to_latex_table('simulation_difficulties_c4.csv', 'output_latex.tex')