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
gamma = Decimal(0.5)

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
    eps = []
    for eq in nash_eqs:
        for player, strategies in eq.items():
            expected_payoff = 0
            if player == 'Alice':
                for alice_idx, (alice_strategy, alice_prob) in enumerate(strategies):
                    alice_strategy = [float(x // intvl) for x in alice_strategy]
                    for bob_idx, (bob_strategy, bob_prob) in enumerate(eq['Bob']):
                        bob_strategy = [float(x // intvl) for x in bob_strategy]
                        payoff = get_payoff_element(alice_strategy, bob_strategy, num_plays, K, D, intvl, gamma, bob = False)
                        expected_payoff += Decimal(alice_prob) * Decimal(bob_prob) * payoff
                alice_ep = expected_payoff

            elif player == 'Bob':
                for bob_idx, (bob_strategy, bob_prob) in enumerate(strategies):
                    bob_strategy = [float(x // intvl) for x in bob_strategy]
                    for alice_idx, (alice_strategy, alice_prob) in enumerate(eq['Alice']):
                        alice_strategy = [float(x // intvl) for x in alice_strategy]
                        payoff = get_payoff_element(alice_strategy, bob_strategy, num_plays, K, D, intvl, gamma, bob = True)
                        expected_payoff += Decimal(bob_prob) * Decimal(alice_prob) * payoff
                bob_ep = expected_payoff
        
        eps.append((alice_ep, bob_ep))

    return eps

def choose_eq(nash_eqs: list, eps: list) -> dict:
    if len(nash_eqs) == 1:
        return nash_eqs[0]
    
    for idx, ep in enumerate(eps):
        if ep[0] == max(ep[0] for ep in eps) and ep[1] == max(ep[1] for ep in eps):
            return nash_eqs[idx]
    
    max_min_payoff_idx = max(
        range(len(eps)), 
        key = lambda i: min(eps[i][0], eps[i][1])
    )
    return nash_eqs[max_min_payoff_idx]
                      