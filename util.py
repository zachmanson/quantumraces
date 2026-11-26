from pathlib import Path

SEPARATOR = '-------------'


def write_equilibrium(path, alice_mixed: dict, bob_mixed: dict) -> None:
    """Write one equilibrium: a line 'Player [k_1, ..., k_c] probability' per support strategy."""
    with open(path, 'w') as f:
        for player, mixed in (('Alice', alice_mixed), ('Bob', bob_mixed)):
            for strat, prob in mixed.items():
                print(f"{player} [{', '.join(str(int(k)) for k in strat)}] {prob!r}", file=f)
        print(SEPARATOR, file=f)


def write_equilibria(base_path, equilibria: list, stop_after: int) -> list[Path]:
    """Write one file per equilibrium: base.txt when stop_after == 1, else base_eq1.txt, base_eq2.txt, ..."""
    base_path = Path(base_path)
    if stop_after == 1:
        paths = [base_path.with_name(base_path.name + '.txt')]
    else:
        paths = [base_path.with_name(f'{base_path.name}_eq{n}.txt') for n in range(1, len(equilibria) + 1)]
    for path, (alice_mixed, bob_mixed) in zip(paths, equilibria):
        write_equilibrium(path, alice_mixed, bob_mixed)
    return paths


def read_equilibrium(path) -> tuple[dict, dict]:
    """Read a single-equilibrium file into ({strategy: prob} for Alice, {strategy: prob} for Bob)."""
    alice: dict = {}
    bob: dict = {}
    n_separators = 0
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            if line == SEPARATOR:
                n_separators += 1
                continue
            if n_separators:
                raise ValueError(f"{path} holds more than one equilibrium; write one file per equilibrium")
            player, rest = line.split(' ', 1)
            strat_str, prob_str = rest[1:].split(']')
            strat = tuple(int(k) for k in strat_str.split(',') if k.strip())
            (alice if player == 'Alice' else bob)[strat] = float(prob_str)
    return alice, bob
