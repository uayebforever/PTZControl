"""Mapping from raw stick/trigger deflection to commanded camera speed.

Tune the feel of the camera by editing the two constants below.
"""

# Exponent of the power curve applied to |deflection| (0..1).
#   1.0 = linear (no shaping)
#   2.0 = gentle: fine control near centre, moderate ramp at the end
#   3.0 = strong: very fine control over the central range, speed rises
#         steeply as the stick approaches its extreme
# Full deflection always maps to full speed regardless of the exponent.
PAN_TILT_EXPONENT = 2.0
ZOOM_EXPONENT = 2.0


def apply_curve(value: float, exponent: float) -> float:
    """Shape a value in [-1, 1], preserving sign and the 0 / +-1 endpoints."""
    magnitude = min(abs(value), 1.0) ** exponent
    return magnitude if value >= 0 else -magnitude
