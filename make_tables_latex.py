import re

def parse_strategy(strategy_str: str, normalize: bool = False) -> tuple:
    numbers = list(map(int, re.findall(r'np\.int64\((\d+)\)', strategy_str)))
    if normalize:
        return tuple(round(n / 8571866, 5) for n in numbers)
    else:
        return tuple(numbers)

def process_file(input_file: str, output_file: str, normalize: bool = False) -> None:
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
        f.write(r'\begin{tabular}{|l|l|l|}' + '\n')
        f.write(r'\hline' + '\n')
        f.write('Player & Strategy & Probability \\\\ \n')
        f.write(r'\hline' + '\n')

        for i, block in enumerate(blocks):
            for entry in block:
                match = re.match(r'(Alice|Bob)\s+\[(.*?)\]\s+([\d\.eE+-]+)', entry)
                if match:
                    player, strategy_str, probability = match.groups()
                    strategy = parse_strategy(strategy_str, normalize=normalize)
                    if normalize:
                        strategy_latex = '(' + ', '.join(f"{x:.5f}" for x in strategy) + ')'
                    else:
                        strategy_latex = str(strategy)
                    f.write(f'{player} & {strategy_latex} & {probability} \\\\ \n')
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

if __name__ == "__main__":
    # Change normalize to True or False depending on your needs
    process_file('output.txt', 'output_latex.tex', normalize=True)
    check_probability_sums('output.txt')
