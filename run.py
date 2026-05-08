#!/usr/bin/env python3
"""
Unified entry point for the Quantum Races analysis pipeline.

Pipeline: build payoff matrices -> compute Nash equilibrium -> estimate stale rate -> report

D presets:
  high  - Bitcoin difficulty as of May 9 2025 (~1.19e14)
  low   - Bitcoin difficulty as of Feb 26 2013 (~3.65e6)

Examples:
  python run.py
  python run.py --D low --num-plays 2 --n-q 25
  python run.py --D 5000000 --plot-heatmap
  python run.py --plot-stale-difficulty --num-simulations 100000
  python run.py --plot-stale-budget --n-q 20 --num-plays 2
"""

import argparse
import os
import sys

import numpy as np

from buildpayoff import BuildPayoff
from analyze_nasheqs import NashEquilibriaAnalyzer
from simulate_mining import QuantumMiningSimulator
from util import parse_nash_eq_from_file

D_HIGH = 119116256505723.5   # Bitcoin difficulty as of May 9 2025
D_LOW  = 3651011.631          # Bitcoin difficulty as of Feb 26 2013

RESULTS_DIR = 'results'
IMAGES_DIR  = 'images'


def parse_args():
    parser = argparse.ArgumentParser(
        description='Quantum mining game: build payoff -> Nash eq -> stale rate estimation.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument(
        '--D', default='high',
        help="Difficulty: 'high' (current, ~1.19e14), 'low' (2013, ~3.65e6), or a numeric value. Default: high"
    )
    parser.add_argument('--num-plays', '-c', type=int, default=3,
                        help='Number of Grover search plays (default: 3)')
    parser.add_argument('--n-q', type=int, default=34, dest='n_q',
                        help='Number of grid points for strategy discretization (default: 34)')
    parser.add_argument('--gamma', type=float, default=0.5,
                        help='Payoff split parameter (default: 0.5)')
    parser.add_argument('--clustering-factor', type=float, default=2.0,
                        help='Grid clustering factor (default: 2.0)')
    parser.add_argument('--num-simulations', type=int, default=1000000,
                        help='Number of Monte Carlo simulations (default: 1000000)')
    parser.add_argument('--stop-after', type=int, default=1,
                        help='Stop after N Nash equilibria (default: 1)')
    parser.add_argument('--scale-with-D', action='store_true',
                        help='Scale max iterations with D instead of capping at 2^32 (default: False)')
    parser.add_argument('--plot-heatmap', action='store_true',
                        help='Plot Nash equilibrium strategy heatmaps')
    parser.add_argument('--plot-stale-difficulty', action='store_true',
                        help='Sweep difficulties c=1..4 and plot stale rate vs difficulty')
    parser.add_argument('--plot-stale-budget', action='store_true',
                        help='Sweep budget multipliers and plot stale rate vs budget')
    parser.add_argument('--no-simulate', action='store_true',
                        help='Skip Monte Carlo simulation, only compute Nash equilibrium')
    parser.add_argument('--compute-ep', action='store_true',
                        help='Compute and print expected payoffs (use with --simulate-from)')
    parser.add_argument('--simulate-from', metavar='FILE',
                        help='Skip pipeline, load Nash eq from FILE and run simulation only')
    return parser.parse_args()


def resolve_D(d_arg: str) -> float:
    if d_arg == 'high':
        return D_HIGH
    if d_arg == 'low':
        return D_LOW
    try:
        return float(d_arg)
    except ValueError:
        print(f"Error: --D must be 'high', 'low', or a numeric value. Got: {d_arg!r}")
        sys.exit(1)


def _difficulty_label(D: float, scale_with_D: bool) -> str:
    if D == D_LOW:
        return "low"
    elif scale_with_D:
        return "ideal"
    return "high"


def run_simulate(nash_fname, num_simulations, D, scale_with_D=False,
                 plot_heatmap=False, compute_ep=False, gamma=0.5, no_simulate=False):
    """Load a Nash eq file and run the Monte Carlo simulation."""

    # Determine difficulty label
    difficulty_label = _difficulty_label(D, scale_with_D)

    # Compute expected payoffs if requested
    if compute_ep:
        print(f"\n{'='*60}")
        print("Computing expected payoffs")
        print(f"{'='*60}")
        alice_mixed, bob_mixed = parse_nash_eq_from_file(nash_fname)
        all_iters = [v for strat in list(alice_mixed.keys()) + list(bob_mixed.keys()) for v in strat]
        if all_iters:
            num_plays = len(next(iter(alice_mixed.keys())))
            max_iters = max(all_iters)
            ep_builder = BuildPayoff(
                n_q=max_iters, num_plays=num_plays, D=D,
                clustering_factor=1.0, gamma=gamma,
                scale_with_D=False
            )
            alice_ep = ep_builder.compute_expected_payoff(alice_mixed, bob_mixed, player="Alice")
            bob_ep   = ep_builder.compute_expected_payoff(alice_mixed, bob_mixed, player="Bob")
            print(f"  Alice expected payoff: {alice_ep:.6f}")
            print(f"  Bob expected payoff:   {bob_ep:.6f}")
        else:
            print("  No strategies found in Nash eq file.")

    # Plot heatmap if requested
    if plot_heatmap:
        norm_factor = int(np.floor(np.pi / 4 * np.sqrt(min(D, 2**32))))
        from visualize_nash_eq import visualize_nash_equilibria_discrete_file
        visualize_nash_equilibria_discrete_file(
            nash_fname,
            normalization_factor=norm_factor,
            difficulty_label=difficulty_label,
        )

    # Skip simulation if requested
    if no_simulate:
        return None, None, None

    analyzer = NashEquilibriaAnalyzer()
    nash_eq = analyzer.converge(nash_fname)
    simulator = QuantumMiningSimulator(
        nash_eq, num_simulations=num_simulations, difficulty=D, scale_with_D=scale_with_D
    )
    avg_fork_rate, avg_blocks, avg_forks = simulator.simulate_all()
    print(f"\n{'='*60}")
    print("Results")
    print(f"{'='*60}")
    print(f"  Stale rate:          {avg_fork_rate:.6f}")
    print(f"  Avg blocks/day:      {avg_blocks:.2f}")
    print(f"  Avg forks/day:       {avg_forks:.2f}")
    return avg_fork_rate, avg_blocks, avg_forks


def run_pipeline(D, num_plays, n_q, gamma, clustering_factor, num_simulations, stop_after,
                 scale_with_D=False, plot_heatmap=False, no_simulate=False):
    """Run the full pipeline for a single (D, num_plays, n_q) configuration."""
    os.makedirs(RESULTS_DIR, exist_ok=True)
    os.makedirs(IMAGES_DIR, exist_ok=True)
    nash_fname = os.path.join(RESULTS_DIR, 'nash_eq.txt')

    # --- Config summary ---
    print(f"\n{'='*60}")
    print("Configuration")
    print(f"{'='*60}")
    print(f"  D (difficulty):      {D:.6g}  ({'high' if D == D_HIGH else 'low' if D == D_LOW else 'custom'})")
    print(f"  c (num_plays):       {num_plays}")
    print(f"  n_q (grid points):   {n_q}")
    print(f"  gamma:               {gamma}")
    print(f"  clustering_factor:   {clustering_factor}")
    print(f"  num_simulations:     {num_simulations:,}")
    print(f"  scale_with_D:        {scale_with_D}")

    # --- Build payoff matrices ---
    print(f"\n{'='*60}")
    print("Building payoff matrices")
    print(f"{'='*60}")
    builder = BuildPayoff(
        n_q, num_plays, D, clustering_factor, gamma,
        out_fname=nash_fname,
        scale_with_D=scale_with_D,
        stop_after=stop_after
    )
    A = builder.get_payoff()
    B = builder.get_payoff(bob=True)
    A, B = builder.eliminate_dominated(A, B)

    # --- Compute Nash equilibrium ---
    print("\nComputing Nash equilibrium...")
    builder.get_nash_eq_pygambit(A, B)
    print(f"Nash equilibrium written to: {nash_fname}")

    # --- Expected payoffs ---
    print("\nComputing expected payoffs...")
    alice_mixed, bob_mixed = parse_nash_eq_from_file(nash_fname)
    all_iters = [v for strat in list(alice_mixed.keys()) + list(bob_mixed.keys()) for v in strat]
    if all_iters:
        max_iters = max(all_iters)
        ep_builder = BuildPayoff(
            n_q=max_iters, num_plays=num_plays, D=D,
            clustering_factor=1.0, gamma=gamma,
            scale_with_D=False
        )
        alice_ep = ep_builder.compute_expected_payoff(alice_mixed, bob_mixed, player="Alice")
        bob_ep   = ep_builder.compute_expected_payoff(alice_mixed, bob_mixed, player="Bob")
        print(f"  Alice expected payoff: {alice_ep:.6f}")
        print(f"  Bob expected payoff:   {bob_ep:.6f}")

    # --- Optional: heatmap ---
    if plot_heatmap:
        from visualize_nash_eq import visualize_nash_equilibria_discrete_file
        visualize_nash_equilibria_discrete_file(nash_fname)

    if no_simulate:
        print("\nSkipping simulation (--no-simulate).")
        return None, None, None

    # --- Simulate stale rate ---
    return run_simulate(nash_fname, num_simulations, D, scale_with_D)


def main():
    args = parse_args()
    D = resolve_D(args.D)

    if args.simulate_from:
        if not os.path.exists(args.simulate_from):
            print(f"Error: file not found: {args.simulate_from}")
            sys.exit(1)
        print(f"Loading Nash equilibrium from: {args.simulate_from}")
        run_simulate(
            args.simulate_from,
            args.num_simulations,
            D,
            scale_with_D=args.scale_with_D,
            plot_heatmap=args.plot_heatmap,
            compute_ep=args.compute_ep,
            gamma=args.gamma,
            no_simulate=args.no_simulate,
        )
    else:
        run_pipeline(
            D=D,
            num_plays=args.num_plays,
            n_q=args.n_q,
            gamma=args.gamma,
            clustering_factor=args.clustering_factor,
            num_simulations=args.num_simulations,
            stop_after=args.stop_after,
            scale_with_D=args.scale_with_D,
            plot_heatmap=args.plot_heatmap,
            no_simulate=args.no_simulate,
        )

    if args.plot_stale_difficulty:
        print(f"\n{'='*60}")
        print("Stale rate vs difficulty sweep (c=1..4)")
        print(f"{'='*60}")
        from simulate_mining import simulate_multiple_strategies
        simulate_multiple_strategies(
            num_simulations=args.num_simulations,
            results_dir=RESULTS_DIR,
            images_dir=IMAGES_DIR,
        )

    if args.plot_stale_budget:
        print(f"\n{'='*60}")
        print(f"Stale rate vs budget sweep (c={args.num_plays}, n_q={args.n_q})")
        print(f"{'='*60}")
        from simulate_budgets import run_budget_sweep
        run_budget_sweep(
            n_q=args.n_q,
            num_plays=args.num_plays,
            clustering_factor=args.clustering_factor,
            gamma=args.gamma,
            num_simulations=args.num_simulations,
            results_dir=RESULTS_DIR,
            images_dir=IMAGES_DIR,
        )


if __name__ == '__main__':
    main()
