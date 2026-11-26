import json
import math
import platform
import subprocess
import sys
from importlib.metadata import version
from pathlib import Path

import pandas as pd
import pytest

import buildpayoff as bp

REPO = Path(__file__).resolve().parents[1]


PINNED = [line.split("==")[0] for line in (REPO / "requirements.txt").read_text().splitlines()
          if line and not line.startswith("#")]


def assert_records_versions(record):
    assert record["python"] == platform.python_version()
    assert record["packages"] == {name: version(name) for name in PINNED}     # every pinned package, installed version


def run_cli(*args, cwd):
    result = subprocess.run([sys.executable, str(REPO / "run.py"), *args], cwd=cwd,
                            capture_output=True, text=True, timeout=600)
    assert result.returncode == 0, result.stdout + result.stderr
    return result.stdout


@pytest.mark.slow
def test_pipeline_writes_labelled_outputs_for_a_tiny_full_header_run(tmp_path):
    out = tmp_path / "out"
    stdout = run_cli("--regime", "full-header", "-c", "2", "--n-q", "4", "--num-simulations", "24",
                     "--processes", "2", "--seed", "1", "--out-dir", str(out), cwd=tmp_path)
    assert "561770130060" in stdout                     # kappa printed in the config summary

    meta = json.loads((out / "meta_c2_full-header.json").read_text())
    assert meta["kappa"] == 561770130060 and meta["regime"] == "full-header"
    assert meta["grid"][0] == 0 and meta["grid"][-1] == 561770130060
    eq = meta["equilibria"][0]
    assert 0 <= eq["alice_ep"] <= 1 and 0 <= eq["bob_ep"] <= 1
    assert eq["stats"]["num_days"] == 24
    for player in ("alice", "bob"):
        support = eq[f"{player}_support"]
        mean = [sum(s["probability"] * s["fraction_of_kappa"][i] for s in support) for i in range(2)]
        first = sum(s["probability"] * next((f for f in s["fraction_of_kappa"] if f > 0), 0) for s in support)
        assert eq[f"{player}_schedule"] == pytest.approx(mean)
        assert eq[f"{player}_first_measurement"] == pytest.approx(first)

    assert (out / "nash_eq_c2_full-header.txt").exists()
    assert len(pd.read_csv(out / "simulation_data_c2_full-header.csv")) == 24
    assert (out / "images" / "alice_nash_heatmap_c2_full-header.pdf").exists()
    assert (out / "images" / "bob_nash_heatmap_c2_full-header.pdf").exists()

    # Rerunning resumes from the saved equilibrium and simulation instead of recomputing.
    stdout = run_cli("--regime", "full-header", "-c", "2", "--n-q", "4", "--num-simulations", "24",
                     "--processes", "2", "--seed", "1", "--out-dir", str(out), cwd=tmp_path)
    assert "resuming" in stdout.lower()
    meta = json.loads((out / "meta_c2_full-header.json").read_text())
    assert meta["equilibria"][0]["simulation_s"] > 0          # timing kept on resume
    assert len(meta["commands"]) == 2
    for record in meta["commands"]:                           # each run, resume included, records its versions
        assert_records_versions(record)

    # A different configuration in the same directory must not reuse the old outputs.
    stdout = run_cli("--regime", "full-header", "-c", "2", "--n-q", "5", "--num-simulations", "24",
                     "--processes", "2", "--seed", "2", "--out-dir", str(out), cwd=tmp_path)
    assert "resuming" not in stdout.lower()
    meta = json.loads((out / "meta_c2_full-header.json").read_text())
    assert meta["n_q"] == 5 and meta["equilibria"][0]["seed"] == 2


@pytest.mark.slow
def test_stop_after_two_labels_every_output_per_equilibrium(tmp_path):
    out = tmp_path / "out"
    run_cli("--regime", "nonce-only", "-c", "1", "--n-q", "6", "--stop-after", "2", "--num-simulations", "8",
            "--processes", "2", "--seed", "1", "--out-dir", str(out), cwd=tmp_path)
    meta = json.loads((out / "meta_c1_nonce-only.json").read_text())
    assert meta["equilibria"]
    for n, eq in enumerate(meta["equilibria"], 1):
        assert eq["label"] == f"eq{n}"
        assert (out / f"nash_eq_c1_nonce-only_eq{n}.txt").exists()
        assert (out / f"simulation_data_c1_nonce-only_eq{n}.csv").exists()
        assert (out / "images" / f"nash_heatmap_c1_nonce-only_eq{n}.pdf").exists()


@pytest.mark.slow
def test_control_simulates_days_without_quantum_miners(tmp_path):
    out = tmp_path / "out"
    run_cli("--regime", "full-header", "--control", "--num-simulations", "24", "--processes", "2",
            "--seed", "1", "--out-dir", str(out), cwd=tmp_path)
    meta = json.loads((out / "meta_control.json").read_text())
    assert meta["regime"] == "full-header" and meta["seed"] == 1
    assert_records_versions(meta)
    stats = meta["stats"]
    assert stats["num_days"] == 24
    assert stats["classical_ended_share"] == 1.0          # with no quantum miners every race ends classically
    assert len(pd.read_csv(out / "simulation_data_control.csv")) == 24
    assert not list(out.glob("nash_eq_*"))


@pytest.mark.slow
@pytest.mark.audit
def test_default_gamma_reproduces_the_audit_first_finder_row(tmp_path):
    # Independent audit (2026-10-26) first-finder row, retargeted to n_q = 30 (exact LH, about a minute):
    # full-header, c = 1, gamma_S = 0.6: support size 13, U = 0.4727, E[first measurement] = 0.6875 kappa.
    out = tmp_path / "out"
    run_cli("--regime", "full-header", "-c", "1", "--n-q", "30", "--no-simulate", "--no-plot",
            "--out-dir", str(out), cwd=tmp_path)
    meta = json.loads((out / "meta_c1_full-header.json").read_text())
    assert meta["gamma"] == 0.6
    eq = meta["equilibria"][0]
    assert len(eq["alice_support"]) == 13
    assert eq["alice_ep"] == pytest.approx(0.4727, abs=5e-5)
    assert eq["alice_first_measurement"] == pytest.approx(0.6875, abs=5e-4)


SWEEP_COLUMNS = {"c", "gamma", "n_q", "num_days", "mean_stale_rate", "std_stale_rate", "p95_stale_rate",
                 "p99_stale_rate", "max_stale_rate", "prob_stale_over_third", "prob_stale_over_third_ci_lower",
                 "prob_stale_over_third_ci_upper", "detection_prob_05", "detection_prob_05_ci_lower",
                 "detection_prob_05_ci_upper", "avg_blocks", "avg_stale", "classical_ended_share", "alice_ep",
                 "alice_first_measurement"}


@pytest.mark.slow
def test_gamma_sweep_collects_one_row_per_c_and_gamma_with_plots(tmp_path):
    sweep = tmp_path / "sweep"
    for gamma in ("1.0", "0.5"):
        run_cli("--regime", "full-header", "-c", "1", "--n-q", "4", "--gamma", gamma, "--num-simulations", "24",
                "--processes", "2", "--seed", "1", "--no-plot", "--out-dir", str(sweep / f"g{gamma}"), cwd=tmp_path)
    result = subprocess.run([sys.executable, str(REPO / "sweep_gamma.py"), str(sweep)], cwd=tmp_path,
                            capture_output=True, text=True, timeout=600)
    assert result.returncode == 0, result.stdout + result.stderr

    df = pd.read_csv(sweep / "stale_rate_vs_gamma.csv")
    assert SWEEP_COLUMNS <= set(df.columns)
    assert df["gamma"].tolist() == [0.5, 1.0] and df["c"].tolist() == [1, 1]
    half = df.iloc[0]
    assert half["alice_ep"] == pytest.approx(0.5)              # gamma_S = 1/2: all-in at kappa, payoff 1/2
    assert half["alice_first_measurement"] == pytest.approx(1.0)
    assert (df["num_days"] == 24).all()
    for name in ("p95_stale_rate", "prob_stale_over_third", "detection_prob_05", "mean_stale_rate",
                 "alice_first_measurement"):
        assert (sweep / "images" / f"{name}_vs_gamma.pdf").exists()


@pytest.mark.slow
def test_forks_per_race_writes_one_row_per_equilibrium_and_a_plot(tmp_path):
    res = tmp_path / "res"
    common = ("--regime", "full-header", "-c", "1", "--n-q", "4", "--num-simulations", "24", "--processes", "2",
              "--seed", "1", "--no-plot")
    run_cli(*common, "--gamma", "0.6", "--out-dir", str(res), cwd=tmp_path)
    for gamma in ("1.0", "0.5"):
        run_cli(*common, "--gamma", gamma, "--out-dir", str(res / "sweep" / f"g{gamma}"), cwd=tmp_path)
    result = subprocess.run([sys.executable, str(REPO / "forks_per_race.py"), str(res)], cwd=tmp_path,
                            capture_output=True, text=True, timeout=600)
    assert result.returncode == 0, result.stdout + result.stderr

    df = pd.read_csv(res / "sweep" / "forks_per_race.csv")
    assert sorted(df["source"]) == [".", "sweep/g0.5", "sweep/g1.0"]
    assert {"stale_aqms", "stale_tie", "stale_classical", "stale_baseline", "stale_per_race", "p_aqms_success",
            "aqms_response_fraction", "stale_per_day", "avg_stale", "p95_stale_rate",
            "prob_stale_over_third"} <= set(df.columns)
    # gamma_S = 1/2: both miners go all-in at kappa, so there is no AQMS response and a tie fork needs
    # both to succeed before the classical block (P(T > kappa) = 1/e).
    half = df[df["source"] == "sweep/g0.5"].iloc[0]
    W = bp.W_from_D(bp.D_2025)
    p_kappa = float(bp.success_prob("full-header", W)(bp.kappa("full-header", W)))
    assert half["stale_aqms"] == 0 and half["aqms_responses"] == 0
    assert half["stale_tie"] == pytest.approx(p_kappa**2 / math.e, rel=1e-9)
    assert (res / "sweep" / "images" / "forks_per_race_vs_gamma.pdf").exists()
