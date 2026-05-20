import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401
import tempfile
import os
import pandas as pd

from buildpayoff import BuildPayoff
from analyze_nasheqs import NashEquilibriaAnalyzer
from simulate_mining import QuantumMiningSimulator


class BudgetBuildPayoff(BuildPayoff):
    """BuildPayoff subclass that allows setting max_K (budget) independently of D."""

    def __init__(self, n_q, num_plays, D, clustering_factor, gamma, out_fname, scale_with_D, budget):
        super().__init__(n_q, num_plays, D, clustering_factor, gamma, out_fname, scale_with_D)
        # Override the internally-derived max_K and rebuild the grid for the desired budget
        self.max_K = budget
        self.grid = self.create_quadratic_grid()


def compute_base_max_k(D: float) -> int:
    """Compute the default max_K for scale_with_D=False, matching BuildPayoff logic."""
    return int(np.floor(np.pi / 4 * np.sqrt(min(D, 2**32))))


def run_budget_sweep(n_q=20, num_plays=2, clustering_factor=2.0, gamma=0.5,
                     num_simulations=10000, results_dir='.', images_dir='images'):
    difficulties = [2**exp for exp in range(30, 41)]  # 2^30 to 2^40
    multipliers = np.arange(1.0, 10.5, 0.5)           # 1.0, 1.5, ..., 10.0

    os.makedirs(results_dir, exist_ok=True)
    os.makedirs(images_dir, exist_ok=True)

    print(f"Difficulties: {[f'2^{int(np.log2(d))}' for d in difficulties]}")
    print(f"Budget multipliers: {multipliers.tolist()}")
    print(f"Total combinations: {len(difficulties) * len(multipliers)}")
    print()

    rows = []  # list of dicts for CSV

    for D in difficulties:
        log2_D = int(np.log2(D))
        base_max_k = compute_base_max_k(D)
        print(f"\n{'='*60}")
        print(f"Difficulty: 2^{log2_D}  |  base max_K = {base_max_k}")
        print(f"{'='*60}")

        for multiplier in multipliers:
            budget = int(np.floor(multiplier * base_max_k))
            print(f"  Budget {multiplier:.1f}x  (max_K = {budget})")

            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as tmp:
                tmp_fname = tmp.name

            try:
                builder = BudgetBuildPayoff(
                    n_q, num_plays, D,
                    clustering_factor, gamma,
                    tmp_fname,
                    scale_with_D=False,
                    budget=budget
                )

                A = builder.get_payoff()
                B = builder.get_payoff(bob=True)

                builder.get_nash_eq_pygambit(A, B)
                print("  Nash equilibrium computed.")

                analyzer = NashEquilibriaAnalyzer()
                nash_eq = analyzer.converge(tmp_fname)

                simulator = QuantumMiningSimulator(
                    nash_eq,
                    num_simulations=num_simulations,
                    difficulty=D,
                    scale_with_D=False
                )

                avg_fork_rate, avg_blocks, avg_forks = simulator.simulate_all()
                print(f"  Stale rate: {avg_fork_rate:.6f}")

                rows.append({
                    'log2_difficulty': log2_D,
                    'difficulty': D,
                    'budget_multiplier': multiplier,
                    'max_k': budget,
                    'stale_rate': avg_fork_rate,
                    'avg_blocks': avg_blocks,
                    'avg_forks': avg_forks,
                })

            finally:
                if os.path.exists(tmp_fname):
                    os.remove(tmp_fname)

    # --- Save CSV ---
    df = pd.DataFrame(rows)
    csv_path = os.path.join(results_dir, f'stale_rate_vs_budget_c{num_plays}.csv')
    df.to_csv(csv_path, index=False)
    print(f"\nData saved to {csv_path}")

    # --- 3D Surface Plot ---
    log2_diffs = sorted(df['log2_difficulty'].unique())
    mults = sorted(df['budget_multiplier'].unique())

    X, Y = np.meshgrid(log2_diffs, mults)
    Z = np.zeros_like(X, dtype=float)

    for i, mult in enumerate(mults):
        for j, log2_d in enumerate(log2_diffs):
            val = df.loc[(df['log2_difficulty'] == log2_d) & (df['budget_multiplier'] == mult), 'stale_rate']
            Z[i, j] = val.values[0] if len(val) else np.nan

    fig = plt.figure(figsize=(11, 7))
    ax = fig.add_subplot(111, projection='3d')

    surf = ax.plot_surface(X, Y, Z, cmap='viridis', edgecolor='none', alpha=0.9)
    ax.scatter(X.ravel(), Y.ravel(), Z.ravel(), color='black', s=20, zorder=5)

    ax.set_xlabel(r'$\log_2(D)$', fontsize=11, labelpad=8)
    ax.set_ylabel(r'Budget multiplier', fontsize=11, labelpad=8)
    ax.set_zlabel(r'$p_{\mathrm{stale}}$', fontsize=11, labelpad=8)
    ax.set_title(r'Stale rate vs. difficulty and budget ($c=2$, $n_q=20$)', fontsize=12)

    ax.set_xticks(log2_diffs)
    ax.set_yticks(mults)

    fig.colorbar(surf, ax=ax, shrink=0.5, aspect=10, label=r'$p_{\mathrm{stale}}$')

    plt.tight_layout()
    out_path = os.path.join(images_dir, f'stale_rate_vs_budget_difficulty_c{num_plays}.pdf')
    plt.savefig(out_path, dpi=300)
    print(f"Plot saved to {out_path}")
    plt.show()

    # Print summary table
    print(f"\n{'log2(D)':>8}  {'Multiplier':>10}  {'max_K':>8}  {'Stale Rate':>12}")
    print("-" * 44)
    for row in rows:
        print(f"{row['log2_difficulty']:>8}  {row['budget_multiplier']:>10.1f}  {row['max_k']:>8}  {row['stale_rate']:>12.6f}")


if __name__ == "__main__":
    run_budget_sweep()
