"""Rate limiting ("ramping") of commanded speed.

Tune the feel by editing the two constants below. Speeds are in normalized
units (full range -1..1), so RAMP_UP_PER_SECOND = 4.0 means "from standstill
to full speed in a quarter of a second".
"""

import math

# How quickly commanded speed may increase in magnitude, per second.
# math.inf disables ramping up (speed follows the stick immediately).
RAMP_UP_PER_SECOND = 4.0
# How quickly commanded speed may decrease in magnitude, per second. Kept
# higher than ramp-up so the camera still stops promptly when the stick is
# released. math.inf disables ramping down.
RAMP_DOWN_PER_SECOND = 10.0


class SpeedRamp:
    """Moves a value toward a target no faster than the configured rates."""

    def __init__(
        self, up_per_second: float = RAMP_UP_PER_SECOND, down_per_second: float = RAMP_DOWN_PER_SECOND
    ) -> None:
        self._up = up_per_second
        self._down = down_per_second
        self.value = 0.0

    def step(self, target: float, dt: float) -> float:
        """Advance by dt seconds toward target and return the new value."""
        speeding_up = abs(target) > abs(self.value) and (target * self.value >= 0.0)
        rate = self._up if speeding_up else self._down
        max_delta = rate * dt if math.isfinite(rate) else math.inf
        delta = target - self.value
        if abs(delta) <= max_delta:
            self.value = target
        else:
            self.value += math.copysign(max_delta, delta)
        return self.value

    def reset(self) -> None:
        self.value = 0.0
