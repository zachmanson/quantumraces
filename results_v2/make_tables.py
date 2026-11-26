"""Print the RESULTS_SUMMARY tables from the meta_*.json files in this directory (Markdown on stdout)."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ORDER = [(r, c) for r in ('nonce-only', 'full-header') for c in (1, 2, 3, 4)]


def load():
    metas = []
    for regime, c in ORDER:
        path = HERE / f'meta_c{c}_{regime}.json'
        if path.exists():
            metas.append(json.loads(path.read_text()))
    return metas


def eq_name(m, e):
    return f"c={m['c']} {m['regime']}" + (f" ({e['label']})" if e['label'] else '')


def fmt_s(x):
    return '–' if x is None else f'{x:.1f}'


def main():
    metas = load()
    print('## Runs\n')
    for m in metas:
        for cmd in m['commands']:
            print(f"- `{cmd['command']}` (commit `{cmd['git_commit'][:10]}`, started {cmd['started']})")
    print('\n## Configurations\n')
    print('| regime | c | n_q | κ | \\|S0′\\| | feasible c-tuples | after elimination (A × B) | payoff (s) | elimination (s) | LH (s) | simulation (s) |')
    print('|---|---|---|---|---|---|---|---|---|---|---|')
    for m in metas:
        t = m['timings']
        sims = ', '.join(fmt_s(e.get('simulation_s')) for e in m['equilibria'])
        rows, cols = m['dimension_after_elimination']
        print(f"| {m['regime']} | {m['c']} | {m['n_q']} | {m['kappa']} | {len(m['grid'])} | {m['feasible_strategies']} | "
              f"{rows} × {cols} | {fmt_s(t.get('payoff_s'))} | {fmt_s(t.get('elimination_s'))} | "
              f"{fmt_s(t.get('lemke_howson_s'))} | {sims} |")

    print('\n## Stale rates (1,000,000 simulated days each)\n')
    print('| c | regime | P95 | P99 | max | P(p_stale > 1/3) [95% CI] | P_det [95% CI] | avg blocks/day | avg forks/day | races ended by classical block |')
    print('|---|---|---|---|---|---|---|---|---|---|')
    for m in metas:
        for e in m['equilibria']:
            s = e.get('stats')
            if not s:
                continue
            lo3, hi3 = s['prob_stale_over_third_ci']
            lod, hid = s['detection_prob_05_ci']
            name = m['regime'] + (f" ({e['label']})" if e['label'] else '')
            print(f"| {m['c']} | {name} | {s['p95_stale_rate']:.6f} | {s['p99_stale_rate']:.6f} | {s['max_stale_rate']:.6f} | "
                  f"{s['prob_stale_over_third']:.6f} [{lo3:.6f}, {hi3:.6f}] | {s['detection_prob_05']:.6f} [{lod:.6f}, {hid:.6f}] | "
                  f"{s['avg_blocks']:.4f} | {s['avg_stale']:.4f} | {s['classical_ended_share']:.4f} |")

    print('\n## Expected payoffs at equilibrium\n')
    print('| c | regime | Alice U(σ*) | Bob U(σ*) | Alice (full precision) | Bob (full precision) | symmetric |')
    print('|---|---|---|---|---|---|---|')
    for m in metas:
        for e in m['equilibria']:
            name = m['regime'] + (f" ({e['label']})" if e['label'] else '')
            print(f"| {m['c']} | {name} | {e['alice_ep']:.6f} | {e['bob_ep']:.6f} | {e['alice_ep']:.10e} | {e['bob_ep']:.10e} | {e['symmetric']} |")

    print('\n## Equilibrium supports\n')
    for m in metas:
        for e in m['equilibria']:
            print(f"### {eq_name(m, e)} (symmetric: {e['symmetric']})\n")
            for player in ('alice', 'bob'):
                print(f"{player.capitalize()}:\n")
                print('| probability | iterations | fraction of κ |')
                print('|---|---|---|')
                for s in e[f'{player}_support']:
                    fr = ', '.join(f'{x:.4f}' for x in s['fraction_of_kappa'])
                    print(f"| {s['probability']:.6f} | {s['strategy']} | ({fr}) |")
                print()

    print('## Payoff-matrix numerics\n')
    print('| regime | c | entries | distinct values | min | max | distinct after elimination |')
    print('|---|---|---|---|---|---|---|')
    for m in metas:
        a, r = m['matrix_stats']['A'], m['matrix_stats_reduced']['A']
        print(f"| {m['regime']} | {m['c']} | {a['entries']} | {a['distinct']} | {a['min']:.6e} | {a['max']:.6e} | {r['distinct']} of {r['entries']} |")

    print('\n## Grids S0′\n')
    for m in metas:
        print(f"- {m['regime']}, c={m['c']}, n_q={m['n_q']} ({len(m['grid'])} points): {m['grid']}")


if __name__ == '__main__':
    main()
