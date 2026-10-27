#!/usr/bin/env python3
"""
Collect a gamma_S sweep into one CSV and four plots.

The sweep is a set of run.py outputs, one --out-dir per gamma_S point under SWEEP_DIR (e.g. SWEEP_DIR/g0.60/).
Every meta_c*_*.json found there with simulation stats becomes one row per (c, gamma_S) of
SWEEP_DIR/stale_rate_vs_gamma.csv; points without stats (unfinished or timed out) are skipped.
Plots against gamma_S, one line per c, go to SWEEP_DIR/images/: P95, P_det, mean p_stale and
E[first measurement]/kappa.

Example:
  python sweep_gamma.py results_v2_g06/sweep
"""
import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd

matplotlib.rc('text', usetex=True)
matplotlib.rc('font', family='serif')

PLOTS = {
    'p95_stale_rate': r'95th percentile of $p_{\mathrm{stale}}$',
    'detection_prob_05': r'$P_{\mathrm{det}}$',
    'mean_stale_rate': r'mean $p_{\mathrm{stale}}$',
    'alice_first_measurement': r'$E[\textrm{first measurement}]/\kappa$',
}


def collect(sweep_dir: Path) -> pd.DataFrame:
    rows = []
    for path in sorted(sweep_dir.glob('*/meta_c*_*.json')):
        meta = json.loads(path.read_text())
        eq = (meta.get('equilibria') or [{}])[0]
        stats = eq.get('stats')
        if not stats:
            print(f"  skipping {path} (no simulation stats)")
            continue
        row = {'c': meta['c'], 'gamma': meta['gamma'], 'n_q': meta['n_q'], 'regime': meta['regime'],
               'dimension_after_elimination': 'x'.join(map(str, meta['dimension_after_elimination'])),
               'alice_ep': eq['alice_ep'], 'alice_first_measurement': eq['alice_first_measurement']}
        for key, value in stats.items():
            if isinstance(value, (list, tuple)):
                row[f'{key.removesuffix("_ci")}_ci_lower'], row[f'{key.removesuffix("_ci")}_ci_upper'] = value
            else:
                row[key] = value
        rows.append(row)
    if not rows:
        return pd.DataFrame(columns=['c', 'gamma'])
    return pd.DataFrame(rows).sort_values(['c', 'gamma'], ignore_index=True)


def plot(df: pd.DataFrame, images: Path) -> None:
    images.mkdir(parents=True, exist_ok=True)
    for column, ylabel in PLOTS.items():
        fig, ax = plt.subplots(figsize=(4.5, 3.2))
        for c, group in df.groupby('c'):
            ax.plot(group['gamma'], group[column], marker='o', markersize=3, label=f'$c={c}$')
        ax.set_xlabel(r'$\gamma_S$')
        ax.set_ylabel(ylabel)
        ax.legend()
        fig.tight_layout()
        path = images / f'{column}_vs_gamma.pdf'
        fig.savefig(path)
        plt.close(fig)
        print(f"  Plot saved to {path}")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('sweep_dir', type=Path)
    args = parser.parse_args()
    df = collect(args.sweep_dir)
    csv_path = args.sweep_dir / 'stale_rate_vs_gamma.csv'
    df.to_csv(csv_path, index=False)
    print(f"  {len(df)} rows saved to {csv_path}")
    if len(df):
        plot(df, args.sweep_dir / 'images')


if __name__ == '__main__':
    main()
