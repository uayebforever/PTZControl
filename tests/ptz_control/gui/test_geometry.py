import math

from ptz_control.gui.geometry import clamp_to_unit_disc


def test_inside_disc_unchanged() -> None:
    assert clamp_to_unit_disc(0.3, -0.4) == (0.3, -0.4)


def test_diagonal_corner_clamped_to_circle() -> None:
    x, y = clamp_to_unit_disc(1.0, 1.0)
    assert math.isclose(math.hypot(x, y), 1.0)
    assert x > 0 and y > 0
