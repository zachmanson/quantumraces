import importlib.util
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
RESULTS = REPO / "results_v2_g06"
spec = importlib.util.spec_from_file_location("make_latex_tables", RESULTS / "make_latex_tables.py")
mlt = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mlt)

needs_results = pytest.mark.skipif(not (RESULTS / "meta_control.json").exists(),
                                   reason="results_v2_g06 result files are not on this machine")


def body_rows(table):
    return [line.strip() for line in table.splitlines() if line.strip().endswith(r"\\")]


def test_decimals_is_the_fewest_digits_that_keep_distinct_values_distinct():
    assert mlt.decimals([415.899041, 415.899826, 420.103053]) == 3     # 415.899 vs 415.900
    assert mlt.decimals([0.32051, 0.32054, 0.31891]) == 5              # 0.3205 twice at 4
    assert mlt.decimals([1.0, 1.0, 1.0]) == 0                          # equal values never force digits


def test_decimals_never_goes_below_the_floor():
    assert mlt.decimals([1.0, 1.0], at_least=4) == 4
    assert mlt.decimals([0.12, 0.5], at_least=1) == 1


@needs_results
def test_stale_table_full_header_c1_row_matches_the_headline_run():
    rows = body_rows(mlt.stale_table(RESULTS))
    assert r"1 & full-header & 0.3596 & 0.3698 & 0.4093 & 0.5156 & 1.0000 & 420.103 & 140.488 \\" in rows


@needs_results
def test_stale_table_nonce_only_c3_row_is_the_headline_run_and_sits_at_the_baseline():
    rows = body_rows(mlt.stale_table(RESULTS))
    assert r"3 & nonce-only & 0.0085 & 0.0153 & 0.0464 & 0.0000 & 0.0303 & 144.010 & 0.345 \\" in rows


@needs_results
def test_stale_caption_states_the_simulated_days():
    assert r"averages taken over 1\,000\,000 simulated days" in mlt.stale_table(RESULTS)


@needs_results
def test_stale_table_shows_both_c3_full_header_equilibria_then_the_control_last():
    rows = body_rows(mlt.stale_table(RESULTS))
    i = rows.index(r"3 & full-header$^1$ & 0.3205 & 0.3310 & 0.3679 & 0.0062 & 1.0000 & 415.899 & 122.455 \\")
    assert rows[i + 1] == r"3 & full-header$^2$ & 0.3206 & 0.3311 & 0.3704 & 0.0063 & 1.0000 & 415.900 & 122.461 \\"
    assert rows[-1] == (r"\multicolumn{2}{|l|}{no quantum miner} & 0.0085 & 0.0153 & 0.0455 & 0.0000 & 0.0310 & 143.992 & 0.346 \\")
    assert len(rows) == 1 + 9 + 1  # header, 4 nonce-only + 5 full-header, control


@needs_results
def test_payoff_table_lists_alice_and_bob_per_full_header_equilibrium_to_six_decimals():
    rows = body_rows(mlt.payoff_table(RESULTS))
    assert rows == [
        r"$c$ & Quantum Miner & $U(\sigma^*)$ \\",
        r"1 & Alice & 0.472645 \\", r"1 & Bob & 0.472645 \\",
        r"2 & Alice & 0.476964 \\", r"2 & Bob & 0.476964 \\",
        r"$3^{(1)}$ & Alice & 0.476600 \\", r"$3^{(1)}$ & Bob & 0.476600 \\",
        r"$3^{(2)}$ & Alice & 0.476600 \\", r"$3^{(2)}$ & Bob & 0.476600 \\",
        r"4 & Alice & 0.475131 \\", r"4 & Bob & 0.475131 \\",
    ]
