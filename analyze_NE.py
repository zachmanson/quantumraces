import numpy as np

D = 82047028459932.62

def read_input(fname: str) -> list:
    with open(fname) as reader:
        lines = [line.rstrip('\n') for line in reader]
    return lines

def parse_list(s: str) -> list:
    s = s.strip('[]')
    return [float(x) for x in s.split(',')]

def parse_data(data: list):
    nash_eq = []
    current_eq = {}
    for line in data:
        if line == '-------------':
            if current_eq:
                nash_eq.append(current_eq)
                current_eq = {}
        else:
            player_end = line.index('[')
            list_end = line.index(']')
            
            player = line[:player_end].strip()
            strategy_str = line[player_end:list_end+1]
            value = float(line[list_end+1:].strip())

            strategy = parse_list(strategy_str)
            value = float(value)
            if player in current_eq:
                current_eq[player].append((strategy, value))
            else:
                current_eq[player] = [(strategy, value)]

    if current_eq:
        nash_eq.append(current_eq)

    return nash_eq


def p(k: int) -> float:
    return (math.sin(2 * (k + 1/2) * math.asin(1/np.sqrt(D))))**2

def calculate_expected_payoffs(nash_eqs: list):
    for eq in nash_eqs:
        for player, strategy_info in eq.items():


def main():
    data = read_input('output.txt')
    nash_eqs = parse_data(data)
    calculate_expected_payoffs(nash_eqs)

if __name__ == '__main__':
    main()
