import numpy as np
import math
from buildpayoff import get_payoff_element
from decimal import * 

K = 40 #number of pure strategies
num_plays = 2 #number of plays
D = 82047028459932.62
#D = 52328312063444
max_K = np.floor(np.pi / 4 * np.sqrt(D))
intvl = max_K // K
gamma = 0.5

getcontext().prec = 30 #level of precision in Decimal 


def read_input(fname: str) -> list:
    with open(fname) as reader:
        lines = [line.rstrip('\n') for line in reader]
    return lines

def parse_list(s: str) -> list:
    s = s.strip('[]')
    cleaned_s = s.replace('np.float64(', '').replace(')', '')
    return [float(x) for x in cleaned_s.split(',')]

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
        for player, strategies in eq.items():
            expected_payoff = 0
            if player == 'Alice':
                for alice_idx, (alice_strategy, alice_prob) in enumerate(strategies):
                    for bob_idx, (bob_strategy, bob_prob) in enumerate(eq['Bob']):
                        payoff = get_payoff_element(alice_strategy, bob_strategy, num_plays, K, D, intvl, gamma, bob = False)
                        print(payoff)
                        expected_payoff += Decimal(alice_prob) * Decimal(bob_prob) * payoff
                print(f"Expected payoff for {player}: {expected_payoff}")

            elif player == 'Bob':
                for bob_idx, (bob_strategy, bob_prob) in enumerate(strategies):
                    for alice_idx, (alice_strategy, alice_prob) in enumerate(eq['Alice']):
                        payoff = get_payoff_element(alice_strategy, bob_strategy, num_plays, K, D, intvl, gamma, bob = True)
                        expected_payoff += Decimal(bob_prob) * Decimal(alice_prob) * payoff
                print(f"Expected payoff for {player}: {expected_payoff}")

                                    

def main():
    data = read_input('output.txt')
    nash_eqs = parse_data(data)
    calculate_expected_payoffs(nash_eqs)

if __name__ == '__main__':
    main()
