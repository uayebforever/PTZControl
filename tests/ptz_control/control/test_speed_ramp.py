from ptz_control.control.speed_ramp import SpeedRamp


def test_ramps_up_at_limited_rate():
    ramp = SpeedRamp(up_per_second=2.0, down_per_second=10.0)
    assert ramp.step(1.0, 0.1) == 0.2
    assert ramp.step(1.0, 0.1) == 0.4


def test_reaches_target_without_overshoot():
    ramp = SpeedRamp(up_per_second=2.0, down_per_second=10.0)
    assert ramp.step(0.1, 1.0) == 0.1


def test_ramps_down_faster_and_through_zero_on_reversal():
    ramp = SpeedRamp(up_per_second=2.0, down_per_second=10.0)
    ramp.value = 0.5
    assert ramp.step(-1.0, 0.01) == 0.4  # slows at the down rate first
    assert ramp.step(0.0, 1.0) == 0.0
