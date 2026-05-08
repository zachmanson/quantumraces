import sys, os
import matplotlib
matplotlib.use('Agg')  # non-interactive backend, must come before pyplot import
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from unittest.mock import patch, MagicMock
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
    assert len(saved_paths) == 2

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
    assert len(saved_paths) == 2
