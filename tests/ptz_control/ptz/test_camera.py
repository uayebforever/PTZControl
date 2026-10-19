import pytest

from ptz_control.ptz.camera import PanTiltVelocity, ZoomVelocity


def test_pan_tilt_velocity_stop_is_zero():
    assert PanTiltVelocity.stop() == PanTiltVelocity(pan=0.0, tilt=0.0)


@pytest.mark.parametrize("pan,tilt", [(1.1, 0.0), (-1.1, 0.0), (0.0, 1.1), (0.0, -1.1)])
def test_pan_tilt_velocity_rejects_out_of_range(pan, tilt):
    with pytest.raises(ValueError):
        PanTiltVelocity(pan=pan, tilt=tilt)


def test_zoom_velocity_stop_is_zero():
    assert ZoomVelocity.stop() == ZoomVelocity(value=0.0)


@pytest.mark.parametrize("value", [1.1, -1.1])
def test_zoom_velocity_rejects_out_of_range(value):
    with pytest.raises(ValueError):
        ZoomVelocity(value=value)
