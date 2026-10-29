import importlib.util
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
RESULTS = REPO / "results_v2_g06"
spec = importlib.util.spec_from_file_location("copy_paper_figures", RESULTS / "copy_paper_figures.py")
cpf = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cpf)
needs_results = pytest.mark.skipif(not (RESULTS / "images").is_dir(),
                                   reason="results_v2_g06 result files are not on this machine")


@needs_results
def test_copy_figures_fills_the_folder_with_the_proposed_figures_under_paper_style_names(tmp_path):
    cpf.copy_figures(RESULTS, tmp_path)
    assert sorted(p.name for p in tmp_path.iterdir()) == [
        "alice_nash_heatmap_c2_full-header.pdf",
        "alice_nash_heatmap_c3_full-header_1.pdf",
        "alice_nash_heatmap_c3_full-header_2.pdf",
        "alice_nash_heatmap_c4_full-header.pdf",
        "bob_nash_heatmap_c2_full-header.pdf",
        "bob_nash_heatmap_c3_full-header_1.pdf",
        "bob_nash_heatmap_c3_full-header_2.pdf",
        "bob_nash_heatmap_c4_full-header.pdf",
        "c1_full-header_histogram.pdf",
        "p95_stale_rate_vs_gamma.pdf",
    ]
    eq2 = RESULTS / "c3_stop_after_2" / "images" / "alice_nash_heatmap_c3_full-header_eq2.pdf"
    assert (tmp_path / "alice_nash_heatmap_c3_full-header_2.pdf").read_bytes() == eq2.read_bytes()
