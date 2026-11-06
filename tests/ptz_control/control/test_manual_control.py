import math

from ptz_control.control import speed_ramp
from ptz_control.control.response_curve import PAN_TILT_EXPONENT, apply_curve
from ptz_control.control.manual_control import ManualControlLoop
from ptz_control.input.controller import MotionInput, MotionState
from ptz_control.ptz.camera import PanTiltVelocity, ZoomVelocity
from ptz_control.ptz.mock import MockPTZCamera


class FakeClock:
    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now

    def advance(self, seconds):
        self.now += seconds


def make_loop(motion_input, camera, ramp_up=math.inf, ramp_down=math.inf):
    """Loop with ramping disabled by default so tests can assert exact values."""
    loop = ManualControlLoop(motion_input, camera, clock=FakeClock())
    for ramp in loop._ramps.values():
        ramp._up, ramp._down = ramp_up, ramp_down
    return loop


class FakeMotionInput(MotionInput):
    def __init__(self):
        self.state = MotionState.neutral()

    def open(self) -> None:
        pass

    def close(self) -> None:
        pass

    def poll(self) -> MotionState:
        return self.state


def test_tick_applies_motion_state_to_camera():
    motion_input = FakeMotionInput()
    camera = MockPTZCamera()
    camera.connect()
    loop = make_loop(motion_input, camera)

    motion_input.state = MotionState(pan=0.5, tilt=-0.5, zoom=1.0)
    loop.tick()

    assert camera.velocity == PanTiltVelocity(
        pan=apply_curve(0.5, PAN_TILT_EXPONENT), tilt=-apply_curve(0.5, PAN_TILT_EXPONENT)
    )
    assert camera.zoom_velocity == ZoomVelocity(value=1.0)


def test_small_deflection_is_much_slower_than_linear():
    motion_input = FakeMotionInput()
    camera = MockPTZCamera()
    camera.connect()
    loop = make_loop(motion_input, camera)

    motion_input.state = MotionState(pan=0.3)
    loop.tick()
    assert 0.0 < camera.velocity.pan < 0.3


def test_tick_applies_preset_actions():
    motion_input = FakeMotionInput()
    camera = MockPTZCamera()
    camera.connect()
    loop = make_loop(motion_input, camera)

    motion_input.state = MotionState(preset_recall=4)
    loop.tick()
    assert camera.last_recalled_preset == 4

    motion_input.state = MotionState(preset_save=7)
    loop.tick()
    assert 7 in camera.saved_presets


def test_stop_zeroes_camera_motion():
    motion_input = FakeMotionInput()
    camera = MockPTZCamera()
    camera.connect()
    loop = make_loop(motion_input, camera)

    motion_input.state = MotionState(pan=1.0, tilt=1.0, zoom=1.0)
    loop.tick()
    assert camera.velocity == PanTiltVelocity(pan=1.0, tilt=1.0)

    loop.stop()

    assert camera.velocity == PanTiltVelocity.stop()
    assert camera.zoom_velocity == ZoomVelocity.stop()


def test_ramp_limits_speed_increase_per_tick():
    motion_input = FakeMotionInput()
    camera = MockPTZCamera()
    camera.connect()
    clock = FakeClock()
    loop = ManualControlLoop(motion_input, camera, clock=clock)

    motion_input.state = MotionState(pan=1.0)
    loop.tick()  # first tick has dt=0, so no movement yet
    clock.advance(0.05)
    loop.tick()

    assert 0.0 < camera.velocity.pan <= speed_ramp.RAMP_UP_PER_SECOND * 0.05 + 1e-9

    for _ in range(20):
        clock.advance(0.05)
        loop.tick()
    assert camera.velocity.pan == 1.0


def test_moving_velocity_is_resent_every_tick():
    class CountingCamera(MockPTZCamera):
        moves = 0

        def move(self, velocity):
            self.moves += 1
            super().move(velocity)

    motion_input = FakeMotionInput()
    camera = CountingCamera()
    camera.connect()
    loop = make_loop(motion_input, camera)

    motion_input.state = MotionState(pan=0.5)
    for _ in range(5):
        loop.tick()
    assert camera.moves == 5

    motion_input.state = MotionState()
    loop.tick()
    count = camera.moves
    loop.tick()
    loop.tick()
    assert camera.moves == count  # idle: nothing re-sent
