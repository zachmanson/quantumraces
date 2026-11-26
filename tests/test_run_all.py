import importlib.util
from itertools import groupby
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("run_all", REPO / "results_v2_g06" / "run_all.py")
run_all = importlib.util.module_from_spec(spec)
spec.loader.exec_module(run_all)


def step_and_c(cfg):
    return cfg.step, (cfg.args[cfg.args.index("-c") + 1] if "-c" in cfg.args else None)


def test_batch_runs_the_untimed_c3_second_equilibria_last(tmp_path):
    configs = run_all.plan(tmp_path, smoke=False)
    assert [key for key, _ in groupby(map(step_and_c, configs))] == [
        ("headline", 1), ("headline", 2),
        ("sweep", 1), ("sweep", 2),
        ("control", None),
        ("headline", 3), ("headline", 4),
        ("sweep", 3), ("sweep", 4),
        ("second equilibria", 3),
    ]
    assert [cfg.timeout_s for cfg in configs if cfg.step == "second equilibria"] == [None, None]
    assert all(cfg.timeout_s == run_all.TIMEOUT_S for cfg in configs if cfg.step != "second equilibria")
