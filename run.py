#!/usr/bin/env python3
"""
Unified entry point for the Quantum Races analysis pipeline.

Pipeline: build payoff matrices -> eliminate dominated strategies -> Nash equilibria (Lemke-Howson)
-> expected payoffs -> heatmaps -> Monte Carlo stale-rate simulation, for one (regime, c, n_q) configuration.

Regimes:
  nonce-only   - the oracle searches the 32-bit nonce; kappa = k_opt^32 = 51471
  full-header  - the oracle searches the full header; kappa = k_opt(W)

Each run writes to --out-dir and is resumable: a rerun reuses saved equilibria and simulation data
(use --force to recompute).

Examples:
  python run.py --regime full-header -c 2 --n-q 45
  python run.py --regime nonce-only -c 3 --n-q 35 --stop-after 2
  python run.py --regime nonce-only --simulate-from results_v2/nash_eq_c1_nonce-only.txt
  python run.py --regime full-header --control
"""

import argparse
import json
import shlex
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

import buildpayoff as bp
import simulate_mining as sim
from util import read_equilibrium, write_equilibria

DEFAULT_SEED = 20261025


def parse_args():
    parser = argparse.ArgumentParser(
        description='Quantum mining game: build payoff -> Nash eq -> stale rate estimation.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument('--regime', choices=bp.REGIMES, required=True,
                        help='Mining regime: nonce-only or full-header')
    parser.add_argument('--D', type=float, default=bp.D_2025,
                        help=f'Network difficulty (default: {bp.D_2025}, 9 May 2025)')
    parser.add_argument('--num-plays', '-c', type=int, default=3,
                        help='Number of measurements per race, c (default: 3)')
    parser.add_argument('--n-q', type=int, default=35, dest='n_q',
                        help='Grid resolution: S0\' has up to n_q + 1 iteration counts (default: 35)')
    parser.add_argument('--gamma', type=float, default=0.6,
                        help='gamma_S: probability the first-broadcast block wins an AQMS fork (default: 0.6)')
    parser.add_argument('--stop-after', type=int, default=1,
                        help='Number of Nash equilibria to compute (default: 1)')
    parser.add_argument('--num-simulations', type=int, default=1_000_000,
                        help='Number of simulated days (default: 1000000)')
    parser.add_argument('--seed', type=int, default=DEFAULT_SEED,
                        help=f'Master seed for the simulation (default: {DEFAULT_SEED})')
    parser.add_argument('--processes', type=int, default=None,
                        help='Worker processes for the simulation (default: all CPUs)')
    parser.add_argument('--out-dir', default='results_v2',
                        help='Output directory (default: results_v2)')
    parser.add_argument('--no-simulate', action='store_true',
                        help='Skip the Monte Carlo simulation')
    parser.add_argument('--no-plot', action='store_true',
                        help='Skip the heatmaps')
    parser.add_argument('--force', action='store_true',
                        help='Recompute outputs that already exist')
    parser.add_argument('--control', action='store_true',
                        help='No-quantum-miner control: skip the game and simulate days with the classical network only')
    parser.add_argument('--simulate-from', metavar='FILE',
                        help='Skip the game; load one equilibrium from FILE, then compute payoffs, plots, simulation')
    return parser.parse_args()


def _git_commit() -> str:
    try:
        return subprocess.run(['git', 'rev-parse', 'HEAD'], capture_output=True, text=True,
                              cwd=Path(__file__).resolve().parent).stdout.strip()
    except OSError:
        return 'unknown'


def _command_record() -> dict:
    return {'command': 'python ' + ' '.join(shlex.quote(a) for a in sys.argv), 'git_commit': _git_commit(),
            'started': time.strftime('%Y-%m-%d %H:%M:%S')}


def _matrix_stats(M: np.ndarray) -> dict:
    return {'min': float(M.min()), 'max': float(M.max()), 'entries': int(M.size),
            'distinct': int(np.unique(M).size)}


def _describe_mixed(mixed: dict, kap: int) -> list:
    return [{'strategy': list(s), 'fraction_of_kappa': [k / kap for k in s], 'probability': prob}
            for s, prob in sorted(mixed.items(), key=lambda x: -x[1])]


def solve_game(args, kap, p, grid, base: Path, meta: dict) -> list[Path]:
    """Build the payoff matrices, eliminate dominated strategies and solve; returns equilibrium files."""
    c = args.num_plays
    S = bp.feasible_strategies(grid, c, kap)
    print(f"  |S0'| = {len(grid)}, feasible c-tuples = {len(S)}")

    t0 = time.time()
    A, B = bp.payoff_matrices(S, args.gamma, p)
    meta['timings']['payoff_s'] = time.time() - t0
    meta['matrix_stats'] = {'A': _matrix_stats(A), 'B': _matrix_stats(B)}
    print(f"  Payoff matrices built in {meta['timings']['payoff_s']:.1f}s; "
          f"A in [{A.min():.6e}, {A.max():.6e}], {meta['matrix_stats']['A']['distinct']} distinct values")

    t0 = time.time()
    A, B, rows, cols = bp.eliminate_dominated(A, B)
    meta['timings']['elimination_s'] = time.time() - t0
    meta['dimension_after_elimination'] = [len(rows), len(cols)]
    assert np.array_equal(rows, cols), "symmetric game (B == A.T) must keep the same strategies for both players"
    meta['matrix_stats_reduced'] = {'A': _matrix_stats(A), 'B': _matrix_stats(B)}
    print(f"  After elimination: {len(rows)} x {len(cols)} ({meta['timings']['elimination_s']:.1f}s)")

    print(f"  Lemke-Howson (stop_after={args.stop_after}) started {time.strftime('%Y-%m-%d %H:%M:%S')}", flush=True)
    t0 = time.time()
    equilibria = bp.solve_nash(A, B, args.stop_after)
    meta['timings']['lemke_howson_s'] = time.time() - t0
    print(f"  Lemke-Howson found {len(equilibria)} equilibria in {meta['timings']['lemke_howson_s']:.1f}s")

    mixed = []
    for sa, sb in equilibria:
        alice = {tuple(int(k) for k in S[rows[i]]): float(w) for i, w in enumerate(sa) if w > 0}
        bob = {tuple(int(k) for k in S[cols[j]]): float(w) for j, w in enumerate(sb) if w > 0}
        mixed.append((alice, bob))
    return write_equilibria(base, mixed, args.stop_after)


def analyse_equilibrium(args, W, kap, p, eq_path: Path, label: str, out: Path, previous: dict | None) -> dict:
    """Expected payoffs, heatmaps and simulation for one saved equilibrium."""
    alice, bob = read_equilibrium(eq_path)
    alice_ep, bob_ep = bp.expected_payoffs(alice, bob, args.gamma, p)
    info = {
        'label': label,
        'file': eq_path.name,
        'alice_ep': alice_ep,
        'bob_ep': bob_ep,
        'symmetric': alice == bob,
        'alice_support': _describe_mixed(alice, kap),
        'bob_support': _describe_mixed(bob, kap),
    }
    for player, mixed in (('alice', alice), ('bob', bob)):
        info[f'{player}_schedule'], info[f'{player}_first_measurement'] = bp.measurement_schedule(mixed, kap)
    print(f"\n  [{eq_path.name}] Alice U = {alice_ep:.6f}, Bob U = {bob_ep:.6f}, symmetric = {info['symmetric']}")
    print(f"  E[first measurement]/kappa: Alice {info['alice_first_measurement']:.4f}, "
          f"Bob {info['bob_first_measurement']:.4f}")

    regime_label = args.regime + (f"_{label}" if label else '')
    tag = f"c{args.num_plays}_{regime_label}"
    if not args.no_plot:
        from visualize_nash_eq import visualize_equilibrium
        visualize_equilibrium(eq_path, kap, regime_label, out / 'images')

    if args.no_simulate:
        return info
    csv_path = out / f"simulation_data_{tag}.csv"
    info.update(seed=args.seed, num_days=args.num_simulations)
    reusable = previous and previous.get('stats') and all(previous.get(k) == info[k] for k in ('file', 'seed', 'num_days'))
    if csv_path.exists() and reusable and not args.force:
        print(f"  Resuming: loading simulation data from {csv_path}")
        df = pd.read_csv(csv_path)
        stats = sim.summarise(df['total_blocks'].to_numpy(), df['total_stale'].to_numpy(),
                              df['races'].to_numpy(), df['classical_ended_races'].to_numpy())
        info['simulation_s'] = previous.get('simulation_s')
    else:
        print(f"  Simulating {args.num_simulations:,} days (seed {args.seed})", flush=True)
        t0 = time.time()
        stats = sim.simulate_days(alice, bob, args.regime, W, args.num_simulations, args.seed,
                                  processes=args.processes, csv_path=str(csv_path))
        info['simulation_s'] = time.time() - t0
        print(f"  Simulation time: {info['simulation_s']:.1f}s")
    info['stats'] = stats
    info['csv'] = csv_path.name
    lo3, hi3 = stats['prob_stale_over_third_ci']
    lod, hid = stats['detection_prob_05_ci']
    print(f"  P95 {stats['p95_stale_rate']:.6f}  P99 {stats['p99_stale_rate']:.6f}  max {stats['max_stale_rate']:.6f}")
    print(f"  P(stale > 1/3) {stats['prob_stale_over_third']:.6f} [{lo3:.6f}, {hi3:.6f}]  "
          f"P_det {stats['detection_prob_05']:.6f} [{lod:.6f}, {hid:.6f}]")
    print(f"  Avg blocks/day {stats['avg_blocks']:.4f}  avg stale/day {stats['avg_stale']:.4f}  "
          f"races ended by a classical block {stats['classical_ended_share']:.4f}")
    return info


def run_control(args, W, out: Path) -> None:
    """Simulate days with no quantum miners: the classical baseline for p_stale and P_det."""
    no_quantum = {(): 1.0}
    meta = {
        'regime': args.regime, 'D': args.D, 'W': W, 'seed': args.seed, 'num_simulations': args.num_simulations,
        **_command_record(),
    }
    print(f"\n  Control: simulating {args.num_simulations:,} days without quantum miners (seed {args.seed})", flush=True)
    t0 = time.time()
    meta['stats'] = sim.simulate_days(no_quantum, no_quantum, args.regime, W, args.num_simulations, args.seed,
                                      processes=args.processes, csv_path=str(out / 'simulation_data_control.csv'))
    meta['simulation_s'] = time.time() - t0
    s = meta['stats']
    print(f"  mean p_stale {s['mean_stale_rate']:.6f}  P_det {s['detection_prob_05']:.6f} "
          f"[{s['detection_prob_05_ci'][0]:.6f}, {s['detection_prob_05_ci'][1]:.6f}]")
    meta_path = out / 'meta_control.json'
    meta_path.write_text(json.dumps(meta, indent=2))
    print(f"\nMetadata written to {meta_path}")


def main():
    args = parse_args()
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    W = bp.W_from_D(args.D)
    kap = bp.kappa(args.regime, W)
    p = bp.success_prob(args.regime, W)
    c = args.num_plays

    print(f"\n{'=' * 60}\nConfiguration\n{'=' * 60}")
    print(f"  regime:          {args.regime}")
    print(f"  D:               {args.D!r}")
    print(f"  W:               {W:.6e}")
    print(f"  kappa:           {kap}")
    print(f"  c:               {c}")
    print(f"  n_q:             {args.n_q}")
    print(f"  gamma:           {args.gamma}")
    print(f"  stop_after:      {args.stop_after}")
    print(f"  simulated days:  {args.num_simulations:,}  (seed {args.seed})")
    if args.control:
        run_control(args, W, out)
        return

    # Saved outputs are reused only when they were produced by the same game configuration.
    game_key = {'regime': args.regime, 'c': c, 'n_q': args.n_q, 'D': args.D, 'gamma': args.gamma,
                'stop_after': args.stop_after}
    meta_path = out / f"meta_c{c}_{args.regime}.json"
    meta = json.loads(meta_path.read_text()) if meta_path.exists() and not args.force else {}
    if args.simulate_from or meta.get('game_key') != game_key:
        meta = {}
    grid = bp.grid(args.n_q, kap)
    meta.update(game_key)
    meta.update({
        'game_key': game_key, 'W': W, 'kappa': kap, 'seed': args.seed,
        'num_simulations': args.num_simulations, 'grid': [int(k) for k in grid],
    })
    meta.setdefault('timings', {})
    meta.setdefault('commands', []).append(_command_record())

    if args.simulate_from:
        eq_files = [Path(args.simulate_from)]
        labels = ['']
    else:
        print(f"\n{'=' * 60}\nGame\n{'=' * 60}")
        meta['feasible_strategies'] = len(bp.feasible_strategies(grid, c, kap))
        eq_files = [out / f for f in meta.get('equilibrium_files', [])]
        if eq_files and all(f.exists() for f in eq_files) and not args.force:
            print(f"  Resuming: using saved equilibria {[f.name for f in eq_files]}")
        else:
            eq_files = solve_game(args, kap, p, grid, out / f"nash_eq_c{c}_{args.regime}", meta)
            meta['equilibrium_files'] = [f.name for f in eq_files]
            meta_path.write_text(json.dumps(meta, indent=2))
        labels = [''] if args.stop_after == 1 else [f"eq{n}" for n in range(1, len(eq_files) + 1)]

    print(f"\n{'=' * 60}\nEquilibria\n{'=' * 60}")
    previous = {e['label']: e for e in meta.get('equilibria', [])}
    meta['equilibria'] = [analyse_equilibrium(args, W, kap, p, f, label, out, previous.get(label))
                          for f, label in zip(eq_files, labels)]
    if not args.simulate_from:
        meta_path.write_text(json.dumps(meta, indent=2))
        print(f"\nMetadata written to {meta_path}")


if __name__ == '__main__':
    main()
