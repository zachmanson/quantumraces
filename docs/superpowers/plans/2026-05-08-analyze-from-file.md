# Analyze from Nash Eq File — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Allow `--simulate-from FILE` to also compute expected payoffs and plot heatmaps, controlled by opt-in flags (`--compute-ep`, `--plot-heatmap`, `--no-simulate`).

**Architecture:** Extend `run_simulate` in `run.py` to accept `plot_heatmap`, `compute_ep`, `no_simulate`, and `gamma` parameters. Add a `difficulty_label` parameter to `visualize_nash_equilibria_discrete_file` so the output filename reflects the difficulty regime. Auto-compute `normalization_factor` from `D` in `run.py` rather than relying on the hardcoded default.

**Tech Stack:** Python 3, numpy, matplotlib, existing `BuildPayoff` and `parse_nash_eq_from_file` utilities.

---

### Task 1: Add `difficulty_label` to visualizer and fix output filename

**Files:**
- Modify: `visualize_nash_eq.py`

- [ ] **Step 1: Add `difficulty_label` parameter to `visualize_nash_equilibria_discrete_file`**

Replace the current signature and the hardcoded filename inside `create_discrete_heatmap`. The `normalization_factor` default stays at 1500 for backwards compatibility with direct calls.

Open `visualize_nash_eq.py`. Change line 5:

```python
def visualize_nash_equilibria_discrete_file(filename="output.txt", normalization_factor=1500, difficulty_label="high"):
```

Then update the inner function `create_discrete_heatmap` so it accepts and uses `difficulty_label`. Change its definition (currently `def create_discrete_heatmap(player_name, data, label, normalization_factor):`) to:

```python
def create_discrete_heatmap(player_name, data, label, normalization_factor, difficulty_label):
```

- [ ] **Step 2: Update the hardcoded filename inside `create_discrete_heatmap`**

Find line 97:
```python
plt.savefig(f'images/{player_name.lower()}_nash_heatmap_c{max_len}_low_1.pdf', dpi=300, bbox_inches='tight')
```

Replace with:
```python
plt.savefig(f'images/{player_name.lower()}_nash_heatmap_c{max_len}_{difficulty_label}.pdf', dpi=300, bbox_inches='tight')
```

- [ ] **Step 3: Pass `difficulty_label` through to `create_discrete_heatmap` calls**

At the bottom of `visualize_nash_equilibria_discrete_file` (currently lines 100-103):
```python
    #normalization_factor = 8571866
    normalization_factor = 1500
    create_discrete_heatmap('Alice', alice_data, '(a)', normalization_factor=normalization_factor)
    create_discrete_heatmap('Bob', bob_data, '(b)', normalization_factor=normalization_factor)
```

Replace with (the hardcoded `normalization_factor = 1500` line is removed since it's now in the signature default):
```python
    create_discrete_heatmap('Alice', alice_data, '(a)', normalization_factor=normalization_factor, difficulty_label=difficulty_label)
    create_discrete_heatmap('Bob', bob_data, '(b)', normalization_factor=normalization_factor, difficulty_label=difficulty_label)
```

- [ ] **Step 4: Write a unit test for the filename logic**

Create `tests/test_visualize.py`:

```python
import sys, os
import matplotlib
matplotlib.use('Agg')  # non-interactive backend, must come before pyplot import
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from unittest.mock import patch, MagicMock
import pytest
from visualize_nash_eq import visualize_nash_equilibria_discrete_file

def test_difficulty_label_ideal(tmp_path):
    nash_file = tmp_path / "nash_eq.txt"
    nash_file.write_text("Alice [1] 1.0\nBob [1] 1.0\n-------------\n")
    saved_paths = []
    with patch("matplotlib.pyplot.savefig", side_effect=lambda p, **kw: saved_paths.append(p)), \
         patch("matplotlib.pyplot.show"), \
         patch("matplotlib.pyplot.subplots", return_value=(MagicMock(), MagicMock())), \
         patch("matplotlib.pyplot.tight_layout"):
        visualize_nash_equilibria_discrete_file(str(nash_file), difficulty_label="ideal")
    assert any("ideal" in p for p in saved_paths)

def test_difficulty_label_low(tmp_path):
    nash_file = tmp_path / "nash_eq.txt"
    nash_file.write_text("Alice [1] 1.0\nBob [1] 1.0\n-------------\n")
    saved_paths = []
    with patch("matplotlib.pyplot.savefig", side_effect=lambda p, **kw: saved_paths.append(p)), \
         patch("matplotlib.pyplot.show"), \
         patch("matplotlib.pyplot.subplots", return_value=(MagicMock(), MagicMock())), \
         patch("matplotlib.pyplot.tight_layout"):
        visualize_nash_equilibria_discrete_file(str(nash_file), difficulty_label="low")
    assert any("low" in p for p in saved_paths)
```

- [ ] **Step 5: Run the tests**

```bash
python -m pytest tests/test_visualize.py -v
```

Expected: 2 tests PASS.

- [ ] **Step 6: Commit**

```bash
git add visualize_nash_eq.py tests/test_visualize.py
git commit -m "feat: add difficulty_label param to visualizer, fix output filename"
```

---

### Task 2: Extend `run_simulate` with EP computation, heatmap, and `no_simulate` support

**Files:**
- Modify: `run.py`

- [ ] **Step 1: Update `run_simulate` signature**

Current signature (line 87):
```python
def run_simulate(nash_fname, num_simulations, D, scale_with_D=False):
```

Replace with:
```python
def run_simulate(nash_fname, num_simulations, D, scale_with_D=False,
                 plot_heatmap=False, compute_ep=False, gamma=0.5, no_simulate=False):
```

- [ ] **Step 2: Add difficulty label computation inside `run_simulate`**

Add after the docstring/first line of `run_simulate`, before the existing `analyzer = ...` line:

```python
    if D == D_LOW:
        difficulty_label = "low"
    elif scale_with_D:
        difficulty_label = "ideal"
    else:
        difficulty_label = "high"
```

- [ ] **Step 3: Add expected payoff computation block**

Add after the `difficulty_label` block, before the existing `analyzer = ...` line:

```python
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
```

- [ ] **Step 4: Add heatmap plotting block**

Add after the `compute_ep` block, still before `analyzer = ...`:

```python
    if plot_heatmap:
        norm_factor = int(np.floor(np.pi / 4 * np.sqrt(min(D, 2**32))))
        from visualize_nash_eq import visualize_nash_equilibria_discrete_file
        visualize_nash_equilibria_discrete_file(
            nash_fname,
            normalization_factor=norm_factor,
            difficulty_label=difficulty_label,
        )
```

- [ ] **Step 5: Guard the Monte Carlo simulation with `no_simulate`**

The existing simulation block in `run_simulate` starts at `analyzer = NashEquilibriaAnalyzer()`. Wrap it:

```python
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
```

- [ ] **Step 6: Write a unit test for difficulty label logic**

Add to `tests/test_visualize.py` (or create `tests/test_run.py`):

Create `tests/test_run.py`:

```python
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

D_HIGH = 119116256505723.5
D_LOW  = 3651011.631

def _get_label(D, scale_with_D):
    if D == D_LOW:
        return "low"
    elif scale_with_D:
        return "ideal"
    else:
        return "high"

def test_label_low_no_scale():
    assert _get_label(D_LOW, False) == "low"

def test_label_low_with_scale():
    assert _get_label(D_LOW, True) == "low"

def test_label_high_no_scale():
    assert _get_label(D_HIGH, False) == "high"

def test_label_high_with_scale():
    assert _get_label(D_HIGH, True) == "ideal"

def test_label_custom_no_scale():
    assert _get_label(5_000_000.0, False) == "high"

def test_label_custom_with_scale():
    assert _get_label(5_000_000.0, True) == "ideal"
```

- [ ] **Step 7: Run the tests**

```bash
python -m pytest tests/test_run.py -v
```

Expected: 6 tests PASS.

- [ ] **Step 8: Commit**

```bash
git add run.py tests/test_run.py
git commit -m "feat: extend run_simulate with EP computation, heatmap, and no_simulate support"
```

---

### Task 3: Add `--compute-ep` flag and wire up `main()`

**Files:**
- Modify: `run.py`

- [ ] **Step 1: Add `--compute-ep` to argparse**

In `parse_args()`, add after the `--no-simulate` argument (currently around line 69):

```python
    parser.add_argument('--compute-ep', action='store_true',
                        help='Compute and print expected payoffs (use with --simulate-from)')
```

- [ ] **Step 2: Update the `--simulate-from` dispatch in `main()`**

Current block (lines 175-180):
```python
    if args.simulate_from:
        if not os.path.exists(args.simulate_from):
            print(f"Error: file not found: {args.simulate_from}")
            sys.exit(1)
        print(f"Loading Nash equilibrium from: {args.simulate_from}")
        run_simulate(args.simulate_from, args.num_simulations, D, args.scale_with_D)
```

Replace the `run_simulate` call with:
```python
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
```

- [ ] **Step 3: Smoke test — simulation only (unchanged behaviour)**

Run against an existing Nash eq file (adjust path if needed):
```bash
python run.py --simulate-from results/nash_eq.txt --D high --num-simulations 1000
```

Expected: prints stale rate, avg blocks/day, avg forks/day. No heatmap, no EP output.

- [ ] **Step 4: Smoke test — EP only, no simulation**

```bash
python run.py --simulate-from results/nash_eq.txt --D high --compute-ep --no-simulate
```

Expected: prints "Computing expected payoffs", Alice and Bob EP values. No simulation output.

- [ ] **Step 5: Smoke test — heatmap only, no simulation**

```bash
python run.py --simulate-from results/nash_eq.txt --D high --plot-heatmap --no-simulate
```

Expected: two PDF files written to `images/` with `_high.pdf` suffix. No simulation output.

- [ ] **Step 6: Smoke test — all three together**

```bash
python run.py --simulate-from results/nash_eq.txt --D high --plot-heatmap --compute-ep --num-simulations 1000
```

Expected: EP values printed, PDFs written, stale rate printed.

- [ ] **Step 7: Commit**

```bash
git add run.py
git commit -m "feat: add --compute-ep flag, wire --plot-heatmap and --no-simulate to --simulate-from"
```
