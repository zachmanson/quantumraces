"""Print the paper's stale-rate and payoff tables as LaTeX, read from the meta_*.json files in a results directory.

Replaces table:stalerates, table:expectedpayoffs_low and table:expectedpayoffs_ideal in manuscript_v6.tex.
Reads ROOT/meta_c*_*.json, ROOT/c3_stop_after_2/meta_c3_full-header.json (eq1, eq2) and ROOT/meta_control.json;
ROOT is the first argument (default: this directory).
"""
import json
import sys
from pathlib import Path

# (meta key, header, at least this many digits) per stale-table column after c and regime. The digits shown are the
# fewest that keep the full-header rows distinct (decimals()); nonce-only and control rows differ only by Monte Carlo
# noise around the classical baseline. At least 4 keeps a rate such as P_det = 0.0306 vs the control's 0.0310 readable.
STALE_COLUMNS = (
    ('p95_stale_rate', r'$P_{95}$', 4),
    ('p99_stale_rate', r'$P_{99}$', 4),
    ('max_stale_rate', 'max', 4),
    ('prob_stale_over_third', r'$P\left(p_\text{stale}>\nicefrac13\right)$', 4),
    ('detection_prob_05', r'$P_\text{det}$', 4),
    ('avg_blocks', 'abd', 0),
    ('avg_stale', 'asd', 0),
)


def decimals(values, at_least=0):
    """Fewest decimal digits (at least at_least) at which values that differ still print differently."""
    distinct = sorted(set(values))
    digits = at_least
    while len({f'{v:.{digits}f}' for v in distinct}) < len(distinct):
        digits += 1
    return digits


def read(path):
    return json.loads(Path(path).read_text())


def full_header_equilibria(root, c):
    """The full-header equilibria the paper shows for c: both from the stop_after = 2 run for c = 3, else the headline one."""
    if c == 3:
        return read(Path(root) / 'c3_stop_after_2' / 'meta_c3_full-header.json')['equilibria']
    return read(Path(root) / f'meta_c{c}_full-header.json')['equilibria'][:1]


def stale_rows(root):
    """(c, regime label, stats) per table row: nonce-only and full-header per c, c = 3 full-header as eq1 and eq2."""
    rows = []
    for c in (1, 2, 3, 4):
        rows.append((str(c), 'nonce-only', read(Path(root) / f'meta_c{c}_nonce-only.json')['equilibria'][0]['stats']))
        eqs = full_header_equilibria(root, c)
        rows += [(str(c), 'full-header' + (f'$^{i}$' if len(eqs) > 1 else ''), e['stats']) for i, e in enumerate(eqs, 1)]
    return rows


STALE_CAPTION = r'''Monte Carlo simulation for all computed optimal quantum mining strategies with averages taken over {days} simulated days.
    All values are reported to the fewest decimal digits to ensure distinguishability.
    Each row corresponds to a specific combination of the number of quantum measurements~$c$ and mining regime, where nonce-only/full-header denotes the mining regime and the superscripts distinguish the first and second Nash equilibria for the~$c=3$ full-header case.
    The last row is a simulation of the classical network without quantum miners.
    The reported quantities are the 95th and 99th percentiles~$P_{95}$ and $P_{99}$, the maximum observed stale rate, the empirical probability~$P_{>\nicefrac13}$ that a given day's stale rate exceeds the $\nicefrac13$ benchmark, the empirical detection probability~$P_\text{det}$, and the average blocks (abd) and stale blocks per day (asd).'''


def fmt_row(cells, stats, digits):
    return ' & '.join(cells + [f'{stats[key]:.{d}f}' for (key, _, _), d in zip(STALE_COLUMNS, digits)]) + r' \\'


def d_spec(digits, values):
    """dcolumn spec d{integer digits.decimal digits}, wide enough for the largest value."""
    return f'd{{{len(str(int(max(values))))}.{digits}}}'


def stale_table(root):
    rows = stale_rows(root)
    control = read(Path(root) / 'meta_control.json')['stats']
    every = [stats for _, _, stats in rows] + [control]
    days = {s['num_days'] for s in every}
    if len(days) != 1:
        raise ValueError(f'rows were simulated over different numbers of days: {sorted(days)}')
    caption = STALE_CAPTION.replace('{days}', f'{days.pop():,}'.replace(',', r'\,'))
    full_header = [stats for _, regime, stats in rows if regime.startswith('full-header')]
    digits = [decimals([s[key] for s in full_header], at_least) for key, _, at_least in STALE_COLUMNS]
    spec = ' | '.join(['c', 'l'] + [d_spec(d, [s[key] for s in every]) for (key, _, _), d in zip(STALE_COLUMNS, digits)])
    header = ' & '.join(['$c$', 'regime'] + [rf'\multicolumn{{1}}{{c|}}{{{h}}}' for _, h, _ in STALE_COLUMNS]) + r' \\'
    lines = [r'\begin{table}[ht]', r'    \centering', rf'\begin{{tabular}}{{| {spec} |}}', r'\hline', header, r'\hline']
    for i, (c, regime, stats) in enumerate(rows):
        if i and c != rows[i - 1][0]:
            lines.append(r'\hline')
        lines.append(fmt_row([c, regime], stats, digits))
    lines += [r'\hline', fmt_row([r'\multicolumn{2}{|l|}{no quantum miner}'], control, digits), r'\hline', r'\end{tabular}', '',
              rf'    \caption{{{caption}', r'    }', r'    \label{table:stalerates}', r'\end{table}']
    return '\n'.join(lines)


PAYOFF_CAPTION = r'''Alice's and Bob's expected payoffs~$U(\sigma^*)$ for each computed optimal quantum mining strategy in the full-header regime.
    The superscripts $(1)$ and $(2)$ denote the two distinct Nash equilibria computed for $c=3$.'''


def payoff_table(root):
    """Full-header only: the nonce-only payoff is the same tiny value for every c and goes in the text."""
    lines = [r'\begin{table}[H]', r'    \centering', r'      \begin{tabular}{c c c}', r'          $c$ & Quantum Miner & $U(\sigma^*)$ \\']
    for c in (1, 2, 3, 4):
        eqs = full_header_equilibria(root, c)
        for i, e in enumerate(eqs, 1):
            name = f'${c}^{{({i})}}$' if len(eqs) > 1 else str(c)
            lines += [rf'          {name} & Alice & {e["alice_ep"]:.6f} \\', rf'          {name} & Bob & {e["bob_ep"]:.6f} \\']
        lines.append(r'          \hline')
    lines += [r'      \end{tabular}', rf'    \caption{{{PAYOFF_CAPTION}}}', r'    \label{table:expectedpayoffs}', r'\end{table}']
    return '\n'.join(lines)


def main():
    root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parent
    if not root.is_dir():
        sys.exit(f'No such results directory: {root}')
    print(payoff_table(root))
    print()
    print(stale_table(root))


if __name__ == '__main__':
    main()
