from ptz_control.control.manual_control import ManualControlLoop
from ptz_control.input.controller import MotionInput, MotionState
from ptz_control.ptz.camera import PanTiltVelocity, ZoomVelocity
from ptz_control.ptz.mock import MockPTZCamera


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
    loop = ManualControlLoop(motion_input, camera)

    motion_input.state = MotionState(pan=0.5, tilt=-0.5, zoom=1.0)
    loop.tick()

    assert camera.velocity == PanTiltVelocity(pan=0.5, tilt=-0.5)
    assert camera.zoom_velocity == ZoomVelocity(value=1.0)


def test_tick_applies_preset_actions():
    motion_input = FakeMotionInput()
    camera = MockPTZCamera()
    camera.connect()
    loop = ManualControlLoop(motion_input, camera)

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
    loop = ManualControlLoop(motion_input, camera)

    motion_input.state = MotionState(pan=1.0, tilt=1.0, zoom=1.0)
    loop.tick()
    assert camera.velocity == PanTiltVelocity(pan=1.0, tilt=1.0)

    loop.stop()

    assert camera.velocity == PanTiltVelocity.stop()
    assert camera.zoom_velocity == ZoomVelocity.stop()
