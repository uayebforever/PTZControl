"""Qt-free geometry helpers for the GUI."""


def clamp_to_unit_disc(x: float, y: float) -> tuple[float, float]:
    """Scale (x, y) down onto the unit circle if it lies outside it."""
    length = (x * x + y * y) ** 0.5
    if length > 1.0:
        return x / length, y / length
    return x, y
