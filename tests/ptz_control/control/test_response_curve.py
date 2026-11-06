from ptz_control.control.response_curve import apply_curve


def test_endpoints_preserved():
    for exponent in (1.0, 2.0, 3.0):
        assert apply_curve(0.0, exponent) == 0.0
        assert apply_curve(1.0, exponent) == 1.0
        assert apply_curve(-1.0, exponent) == -1.0


def test_symmetric_and_monotonic():
    assert apply_curve(-0.4, 3.0) == -apply_curve(0.4, 3.0)
    assert apply_curve(0.4, 3.0) < apply_curve(0.6, 3.0)


def test_linear_exponent_is_identity():
    assert apply_curve(0.37, 1.0) == 0.37
