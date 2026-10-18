import time

from ptz_control.control.manual_control import ManualControlLoop
from ptz_control.input.controller import MotionInput, MotionState
from ptz_control.ptz.camera import PanTiltVelocity, ZoomVelocity
from ptz_control.ptz.mock import MockPTZCamera


class FakeMotionInput(MotionInput):
    def __init__(self):
        self.state = MotionState.neutral()
        self.opened = False
        self.closed = False

    def open(self) -> None:
        self.opened = True

    def close(self) -> None:
        self.closed = True

    def poll(self) -> MotionState:
        return self.state


def _wait_until(predicate, timeout=2.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(0.01)
    return False


def test_control_loop_applies_motion_state_to_camera():
    motion_input = FakeMotionInput()
    camera = MockPTZCamera()
    camera.connect()

    loop = ManualControlLoop(motion_input, camera, poll_hz=200.0)
    loop.start()
    try:
        motion_input.state = MotionState(pan=0.5, tilt=-0.5, zoom=1.0)

        assert _wait_until(lambda: camera.velocity == PanTiltVelocity(pan=0.5, tilt=-0.5))
        assert camera.zoom_velocity == ZoomVelocity(value=1.0)
    finally:
        loop.stop()


def test_control_loop_applies_preset_actions():
    motion_input = FakeMotionInput()
    camera = MockPTZCamera()
    camera.connect()

    loop = ManualControlLoop(motion_input, camera, poll_hz=200.0)
    loop.start()
    try:
        motion_input.state = MotionState(preset_recall=4)
        assert _wait_until(lambda: camera.last_recalled_preset == 4)

        motion_input.state = MotionState(preset_save=7)
        assert _wait_until(lambda: 7 in camera.saved_presets)
    finally:
        loop.stop()


def test_stop_zeroes_camera_motion():
    motion_input = FakeMotionInput()
    camera = MockPTZCamera()
    camera.connect()

    loop = ManualControlLoop(motion_input, camera, poll_hz=200.0)
    loop.start()
    motion_input.state = MotionState(pan=1.0, tilt=1.0, zoom=1.0)
    assert _wait_until(lambda: camera.velocity == PanTiltVelocity(pan=1.0, tilt=1.0))

    loop.stop()

    assert camera.velocity == PanTiltVelocity.stop()
    assert camera.zoom_velocity == ZoomVelocity.stop()
    assert not loop.is_running
