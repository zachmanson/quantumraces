# Quantum Races

Code accompanying the paper *Strategies for Quantum-Enabled Bitcoin Miners*.

Given the input parameters, this code populates the payoff matrices for our two-player quantum racing model, computes Nash equilibria (via the Lemke–Howson algorithm), and estimates the effect of these Nash equilibria on the Bitcoin network via Monte Carlo simulation.

## Data

The data used to produce the results of this paper is found in `data/`. This includes the Nash equilibrium files (`.txt`) and raw simulation outputs (`.csv`) for each configuration of $c$ and difficulty regime used.

## Installation

```bash
pip install -r requirements.txt
```

## Usage

`run.py` runs the full pipeline (build payoff matrices → compute Nash equilibrium → simulate), or can run individual stages.

```bash
python run.py [options]
```

### Parameters

| Flag | Default | Description |
|------|---------|-------------|
| `--D` | `high` | Difficulty: `high` (~1.19×10¹⁴, Bitcoin May 2025), `low` (~3.65×10⁶, Bitcoin 2013), `ideal` (high D with uncapped Grover iterations), or a numeric value |
| `-c`, `--num-plays` | `3` | Number of Grover search plays |
| `--n-q` | `35` | Number of grid points for strategy discretisation |
| `--gamma` | `0.5` | Sattath's propagation parameter |
| `--clustering-factor` | `2.0` | Controls the clustering of grid points in the discretized straetgy space (higher = denser at high iteration counts) |
| `--num-simulations` | `1,000,000` | Number of Monte Carlo simulations |
| `--scale-with-D` | off | Scale max Grover iterations with D instead of capping at 2³² |

### Common usages

```bash
# Full pipeline (default: c=3, high D)
python run.py

# Low difficulty, c=1
python run.py --D low -c 1 --n-q 50

# Ideal difficulty, c=1, plot Nash equilibrium heatmaps only
python run.py --D ideal -c 1 --n-q 50 --plot-heatmap --no-simulate

# Skip the pipeline and simulate from a saved Nash equilibrium
python run.py --simulate-from data/c1_low.txt --D low

# Sweep over difficulties c=1..4 and produce the P₉₅ / Pdet plots
python run.py --plot-stale-difficulty
```

## Outputs

- `results/nash_eq.txt` — Nash equilibrium for the most recent pipeline run
- `data/simulation_data_c{c}_{D}.csv` — raw Monte Carlo simulation data
- `images/` — all plots (Nash equilibrium heatmaps, sweep figures)

---

*Claude (Anthropic) was used in this repository for improving code efficiency, refactoring, and writing the plotting code. All core logic, mathematics, and modelling is my own work.*
