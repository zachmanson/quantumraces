import numpy as np
import math
from decimal import Decimal, getcontext
from buildpayoff import get_payoff_element

class NashEquilibriaAnalyzer:
    def __init__(self,
                 K: int = 40,
                 num_plays: int = 2,
                 D: float = 82047028459932.62,
                 gamma: Decimal = Decimal(0.5)) -> None:
        
        self.K = K
        self.num_plays = num_plays
        self.D = D
        self.max_K = np.floor(np.pi / 4 * np.sqrt(D))
        self.intvl = self.max_K // self.K
        self.gamma = gamma
        getcontext().prec = 30 #level of precision in Decimal


    def read_input(self, fname = str) -> list[str]:
        with open(fname) as reader:
            lines = [line.rstrip('\n') for line in reader]
        return lines
    
    def parse_list(self, s: str) -> list[float]:
        s = s.strip('[]')
        cleaned_s = s.replace('np.float64(', '').replace(')', '')
        return [float(x) for x in cleaned_s.split(',')]
    
    def parse_data(self, data: list[str]) -> list[dict[str, list[tuple[list[float], float]]]]:
        nash_eq = []
        current_eq: dict[str, list[tuple[list[float], float]]] = {}
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
    
                strategy = self.parse_list(strategy_str)
                value = float(value)
                if player in current_eq:
                    current_eq[player].append((strategy, value))
                else:
                    current_eq[player] = [(strategy, value)]

        if current_eq:
            nash_eq.append(current_eq)

        return nash_eq
    
    def p(self, k: int) -> float:
        return (math.sin(2 * (k + 1/2) * math.asin(1/np.sqrt(self.D)))**2)
    
    def calculate_expected_payoffs(self, nash_eqs: list[dict[str, list[tuple[list[float], float]]]]) -> list:
        eps = []
        for eq in nash_eqs:
            for player, strategies in eq.items():
                expected_payoff = Decimal(0)
                if player == 'Alice':
                    for alice_idx, (alice_strategy, alice_prob) in enumerate(strategies):
                        alice_strategy = [float(x // self.intvl) for x in alice_strategy]
                        for bob_idx, (bob_strategy, bob_prob) in enumerate(eq['Bob']):
                            bob_strategy = [float(x // self.intvl) for x in bob_strategy]
                            payoff = get_payoff_element(alice_strategy, bob_strategy, self.num_plays, self.K, self.D, self.intvl, self.gamma, bob = False)
                            expected_payoff += Decimal(alice_prob) * Decimal(bob_prob) * payoff
                    alice_ep = expected_payoff

                elif player == 'Bob':
                    for bob_idx, (bob_strategy, bob_prob) in enumerate(strategies):
                        bob_strategy = [float(x // self.intvl) for x in bob_strategy]
                        for alice_idx, (alice_strategy, alice_prob) in enumerate(eq['Alice']):
                            alice_strategy = [float(x // self.intvl) for x in alice_strategy]
                            payoff = get_payoff_element(alice_strategy, bob_strategy, self.num_plays, self.K, self.D, self.intvl, self.gamma, bob = True)
                            expected_payoff += Decimal(bob_prob) * Decimal(alice_prob) * payoff
                    bob_ep = expected_payoff
            
            eps.append((alice_ep, bob_ep))

        return eps
    def choose_eq(self, nash_eqs: list[dict[str, list[tuple[list[float], float]]]], eps: list[tuple[Decimal, Decimal]]) -> dict[str, list[tuple[list[float], float]]]:
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


    def converge(self, fname: str) -> dict[str, list[tuple[list[float], float]]]:
        data = self.read_input(fname)
        nash_eqs = self.parse_data(data)
        expected_payoffs = self.calculate_expected_payoffs(nash_eqs)
        chosen_eq = self.choose_eq(nash_eqs, expected_payoffs)
        return chosen_eq