import json
import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest

REPO = Path(__file__).resolve().parents[1]


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

    assert (out / "nash_eq_c2_full-header.txt").exists()
    assert len(pd.read_csv(out / "simulation_data_c2_full-header.csv")) == 24
    assert (out / "images" / "alice_nash_heatmap_c2_full-header.pdf").exists()
    assert (out / "images" / "bob_nash_heatmap_c2_full-header.pdf").exists()

    # Rerunning resumes from the saved equilibrium and simulation instead of recomputing.
    stdout = run_cli("--regime", "full-header", "-c", "2", "--n-q", "4", "--num-simulations", "24",
                     "--processes", "2", "--seed", "1", "--out-dir", str(out), cwd=tmp_path)
    assert "resuming" in stdout.lower()


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
