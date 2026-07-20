import random

class NashEquilibriaAnalyzer:
    def __init__(self) -> None:
        pass

    def read_input(self, fname = str) -> list[str]:
        with open(fname) as reader:
            lines = [line.rstrip('\n') for line in reader]
        return lines
    
    def parse_list(self, s: str) -> list[float]:
        s = s.strip('[]')
        cleaned_s = s.replace('np.int64(', '').replace(')', '')
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

    def choose_eq(self, nash_eqs: list[dict[str, list[tuple[list[float], float]]]]) -> dict[str, list[tuple[list[float], float]]]:
        return random.choice(nash_eqs)

    def converge(self, fname: str) -> dict[str, list[tuple[list[float], float]]]:
        data = self.read_input(fname)
        nash_eqs = self.parse_data(data)
        chosen_eq = self.choose_eq(nash_eqs)
        return chosen_eq
