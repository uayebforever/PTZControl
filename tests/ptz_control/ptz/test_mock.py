import pytest

from ptz_control.ptz.camera import PanTiltVelocity, PTZCameraError, ZoomVelocity
from ptz_control.ptz.mock import MockPTZCamera


def test_commands_require_connection():
    camera = MockPTZCamera()
    with pytest.raises(PTZCameraError):
        camera.move(PanTiltVelocity(pan=0.5, tilt=0.0))


def test_connect_disconnect_round_trip():
    camera = MockPTZCamera()
    camera.connect()
    assert camera.connected
    camera.disconnect()
    assert not camera.connected


def test_move_and_zoom_record_last_velocity():
    camera = MockPTZCamera()
    camera.connect()

    camera.move(PanTiltVelocity(pan=0.5, tilt=-0.25))
    camera.zoom(ZoomVelocity(value=0.75))

    assert camera.velocity == PanTiltVelocity(pan=0.5, tilt=-0.25)
    assert camera.zoom_velocity == ZoomVelocity(value=0.75)


def test_stop_zeroes_velocity():
    camera = MockPTZCamera()
    camera.connect()
    camera.move(PanTiltVelocity(pan=1.0, tilt=1.0))
    camera.zoom(ZoomVelocity(value=1.0))

    camera.stop()

    assert camera.velocity == PanTiltVelocity.stop()
    assert camera.zoom_velocity == ZoomVelocity.stop()


def test_presets():
    camera = MockPTZCamera()
    camera.connect()

    camera.save_preset(3)
    camera.recall_preset(3)

    assert camera.saved_presets == {3}
    assert camera.last_recalled_preset == 3
