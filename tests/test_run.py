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
