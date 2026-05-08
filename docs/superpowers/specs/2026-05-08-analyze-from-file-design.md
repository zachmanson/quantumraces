# Design: Analyze from Nash Eq File

**Date:** 2026-05-08

## Goal

Allow `--simulate-from FILE` to also compute expected payoffs and plot heatmaps, controlled by opt-in flags.

## New CLI Flag

- `--compute-ep` (store_true): compute and print Alice + Bob expected payoffs. Only meaningful with `--simulate-from`.

## Existing Flag Extended

- `--plot-heatmap`: already exists for the full pipeline. Now also fires in the `--simulate-from` path.

## Example Usage

```bash
# just simulate (unchanged behaviour)
python run.py --simulate-from results/nash_eq.txt --D high

# simulate + heatmap
python run.py --simulate-from results/nash_eq.txt --D high --plot-heatmap

# simulate + expected payoffs + heatmap
python run.py --simulate-from results/nash_eq.txt --D high --plot-heatmap --compute-ep

# expected payoffs + heatmap, no simulation
python run.py --simulate-from results/nash_eq.txt --D high --no-simulate --plot-heatmap --compute-ep
```

## Changes to `run.py`

### `run_simulate` signature

```python
def run_simulate(nash_fname, num_simulations, D, scale_with_D=False,
                 plot_heatmap=False, compute_ep=False, gamma=0.5):
```

### Difficulty label

Computed once and passed to the visualizer:

```python
if D == D_LOW:
    label = "low"
elif scale_with_D:
    label = "ideal"
else:
    label = "high"
```

### Expected payoff computation

- `num_plays` inferred from the Nash eq file (length of strategy tuples)
- `max_iters` = max iteration value across all strategies in the Nash eq
- Construct `BuildPayoff(n_q=max_iters, num_plays=num_plays, D=D, clustering_factor=1.0, gamma=gamma)`
- Call `compute_expected_payoff` for Alice and Bob, print results

### `--simulate-from` dispatch in `main()`

Pass `plot_heatmap`, `compute_ep`, `gamma`, `scale_with_D`, and `no_simulate` through to `run_simulate`. When `no_simulate=True`, skip the Monte Carlo step but still run EP computation and heatmap if their flags are set.

## Changes to `visualize_nash_eq.py`

### `visualize_nash_equilibria_discrete_file` signature

```python
def visualize_nash_equilibria_discrete_file(filename="output.txt", normalization_factor=1500, difficulty_label="high"):
```

- `normalization_factor`: defaults to 1500 (preserves existing behavior for direct calls). `run.py` always computes and passes the correct value based on D.
- `difficulty_label`: used in the output filename.

### Filename

```python
f'images/{player_name.lower()}_nash_heatmap_c{max_len}_{difficulty_label}.pdf'
```

### `normalization_factor` in `run.py`

Auto-computed before calling the visualizer:

```python
import math
norm_factor = int(math.floor(math.pi / 4 * math.sqrt(min(D, 2**32))))
```

## Parameters Required from User

When using `--simulate-from`, the user must supply:
- `--D` (already required for simulation)
- `--gamma` (optional, default 0.5 — already a CLI arg)
- `--scale-with-D` (optional, default False — already a CLI arg)

`num_plays` is inferred from the file; no new required args.
