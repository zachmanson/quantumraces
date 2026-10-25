# Quantum Races

Code accompanying the paper *Strategies for Quantum-Enabled Bitcoin Miners*.

Given the input parameters, this code builds the payoff matrices for our two-player quantum racing model, computes Nash equilibria (via the Lemke–Howson algorithm), and estimates the effect of these Nash equilibria on the Bitcoin network via Monte Carlo simulation.

## Model in brief

- **Expected work** W = D·2⁴⁸/(2¹⁶−1) hashes per block, from the network difficulty D (default: 119116256505723.5, 9 May 2025).
- **Mining regimes**
  - `nonce-only`: the oracle searches the 32-bit nonce. Success probability is averaged over the Binomial(2³², 1/W) number of valid nonces; budget κ = ⌊π/(4·arcsin 2⁻¹⁶)⌋ = 51471.
  - `full-header`: the oracle searches the full header; marked fraction 1/W; budget κ = ⌊π/(4·arcsin √(1/W))⌋.
- **Strategies**: c-tuples of Grover iteration counts with total ≤ κ, drawn from the grid S0′ = {⌊(1−(1−i/n_q)²)·κ⌋ : i = 0..n_q}.
- **Simulation**: an integer clock in Grover iterations (600/κ s each). Classical blocks arrive as a Poisson process (mean 600 s), and each classical block is stale with the baseline probability 0.0024. Each simulated day has its own random stream derived from a master seed.

`tests/reference_model.py` is the reference implementation of the payoff model; the test suite checks the code against it.

## Installation

```bash
pip install -r requirements.txt
```

Heatmaps use LaTeX text rendering (`usetex`), so a LaTeX installation is needed for plotting.

## Usage

`run.py` runs the full pipeline for one configuration: build payoff matrices → eliminate strictly dominated strategies → Nash equilibria → expected payoffs → heatmaps → simulation.

```bash
python run.py --regime {nonce-only,full-header} [options]
```

### Parameters

| Flag | Default | Description |
|------|---------|-------------|
| `--regime` | (required) | `nonce-only` or `full-header` |
| `--D` | `119116256505723.5` | Network difficulty (blockchain.com units) |
| `-c`, `--num-plays` | `3` | Number of measurements per race |
| `--n-q` | `35` | Grid resolution: S0′ has up to n_q + 1 iteration counts |
| `--gamma` | `0.5` | Sattath's propagation parameter γ_S |
| `--stop-after` | `1` | Number of Nash equilibria to compute; with more than 1, every output is labelled `eqN` |
| `--num-simulations` | `1,000,000` | Number of simulated days |
| `--seed` | `20261025` | Master seed for the simulation |
| `--processes` | all CPUs | Worker processes for the simulation |
| `--out-dir` | `results_v2` | Output directory |
| `--no-simulate`, `--no-plot` | off | Skip the simulation or the heatmaps |
| `--force` | off | Recompute outputs that already exist (runs are otherwise resumable) |
| `--simulate-from FILE` | | Skip the game and analyse a saved equilibrium file |

### Common usages

```bash
# Full-header regime, c = 2
python run.py --regime full-header -c 2 --n-q 45

# Nonce-only, c = 3, first two equilibria
python run.py --regime nonce-only -c 3 --n-q 35 --stop-after 2

# Simulate from a saved equilibrium
python run.py --regime nonce-only --simulate-from results_v2/nash_eq_c1_nonce-only.txt
```

### Tests

```bash
python -m pytest              # everything (the Monte Carlo consistency checks take a few minutes)
python -m pytest -m "not slow"
python tests/reference_model.py
```

## Outputs (in `--out-dir`)

- `nash_eq_c{c}_{regime}.txt` (or `..._eq{N}.txt`): Nash equilibrium supports, one line per pure strategy in Grover iterations
- `meta_c{c}_{regime}.json`: configuration, κ, grid, matrix sizes and statistics, timings, expected payoffs and simulation statistics
- `simulation_data_c{c}_{regime}[_eq{N}].csv`: per-day blocks, stale blocks, races, races ended by a classical block, and binomial p-value
- `images/`: Nash equilibrium heatmaps (c ≥ 2) and the c = 1 histogram

`results_v2/RESULTS_SUMMARY.md` summarises the published runs. Results from the first version of the paper are kept in `archive/v1/`.

---

*Claude (Anthropic) was used in this repository for improving code efficiency, refactoring, and writing the plotting code. All core logic, mathematics, and modelling is my own work.*
