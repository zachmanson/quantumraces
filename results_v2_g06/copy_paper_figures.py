"""Copy the figures proposed for the paper into one folder under the paper's figures/ names, and print the mapping
(old \\includegraphics file -> new file, figure label, caption note) as Markdown for paper-edits.md.

Usage: python results_v2_g06/copy_paper_figures.py [ROOT [DEST]]; ROOT defaults to this directory, DEST to
paper_figures_v2/ at the repo root.
"""
import shutil
import sys
from pathlib import Path

HEATMAP_NOTE = 'shown in the same format as Fig. nasheqheatmaps_2c_ideal'

# (source relative to ROOT, new file name, old file it replaces, figure label, caption note)
FIGURES = (
    ('images/nash_heatmap_c1_full-header.pdf', 'c1_full-header_histogram.pdf', 'c1_ideal_histogram.pdf',
     'fig:nasheqheatmaps_1c_ideal',
     'c = 1 in the full-header regime; takes over the full format description from the deleted fig:nasheqheatmaps_1c_low'),
    *((f'images/{p}_nash_heatmap_c2_full-header.pdf', f'{p}_nash_heatmap_c2_full-header.pdf', f'{p}_nash_heatmap_c2_ideal.pdf',
       'fig:nasheqheatmaps_2c_ideal',
       'c = 2 in the full-header regime; takes over the full format description from the deleted fig:nasheqheatmaps_2c')
      for p in ('alice', 'bob')),
    *((f'c3_stop_after_2/images/{p}_nash_heatmap_c3_full-header_eq1.pdf', f'{p}_nash_heatmap_c3_full-header_1.pdf',
       f'{p}_nash_heatmap_c3_ideal.pdf', 'fig:nasheqheatmaps_3c_ideal',
       f'first Nash equilibrium for c = 3 in the full-header regime (the headline one), {HEATMAP_NOTE}')
      for p in ('alice', 'bob')),
    *((f'c3_stop_after_2/images/{p}_nash_heatmap_c3_full-header_eq2.pdf', f'{p}_nash_heatmap_c3_full-header_2.pdf',
       f'{p}_nash_heatmap_c3_low_2.pdf', 'fig:nasheqheatmaps_3c_low2',
       f'second Nash equilibrium for c = 3 in the full-header regime, {HEATMAP_NOTE}')
      for p in ('alice', 'bob')),
    *((f'images/{p}_nash_heatmap_c4_full-header.pdf', f'{p}_nash_heatmap_c4_full-header.pdf', f'{p}_nash_heatmap_c4_ideal.pdf',
       'fig:nasheqheatmaps_4c_ideal', f'c = 4 in the full-header regime, {HEATMAP_NOTE}')
      for p in ('alice', 'bob')),
    ('sweep/images/p95_stale_rate_vs_gamma.pdf', 'p95_stale_rate_vs_gamma.pdf', '(none; v6 has no figure environment left)',
     'fig:difficultyplots (referenced at ~2876)',
     'new figure: P95 vs γ_S, full-header, c = 1-4, γ_S = 0.50-1.00, 100,000 days per point; needs a new figure environment'),
)


def copy_figures(root, dest):
    root, dest = Path(root), Path(dest)
    dest.mkdir(parents=True, exist_ok=True)
    for source, name, *_ in FIGURES:
        shutil.copy2(root / source, dest / name)


def mapping_table():
    lines = ['| old file | new file | label | caption note |', '|---|---|---|---|']
    lines += [f'| `{old}` | `{name}` | `{label}` | {note} |' for _, name, old, label, note in FIGURES]
    return '\n'.join(lines)


def main():
    root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parent
    dest = Path(sys.argv[2]).resolve() if len(sys.argv) > 2 else Path(__file__).resolve().parents[1] / 'paper_figures_v2'
    copy_figures(root, dest)
    sys.stdout.reconfigure(encoding='utf-8')        # the notes contain γ; the Windows console default is cp1252
    print(mapping_table())


if __name__ == '__main__':
    main()
