import socket

import pytest

from ptz_control.ptz.camera import PanTiltVelocity, PTZCameraError, ZoomVelocity
from ptz_control.ptz.visca import ViscaOverIpCamera


@pytest.fixture
def udp_listener():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("127.0.0.1", 0))
    sock.settimeout(1.0)
    yield sock
    sock.close()


@pytest.fixture
def camera(udp_listener):
    host, port = udp_listener.getsockname()
    cam = ViscaOverIpCamera(host=host, port=port)
    cam.connect()
    yield cam
    cam.disconnect()


def test_move_sends_expected_bytes(camera, udp_listener):
    camera.move(PanTiltVelocity(pan=1.0, tilt=0.0))

    packet, _ = udp_listener.recvfrom(64)

    assert packet == bytes([0x81, 0x01, 0x06, 0x01, 0x18, 0x01, 0x02, 0x03, 0xFF])


def test_move_stop_sends_stop_direction(camera, udp_listener):
    camera.move(PanTiltVelocity.stop())

    packet, _ = udp_listener.recvfrom(64)

    assert packet == bytes([0x81, 0x01, 0x06, 0x01, 0x01, 0x01, 0x03, 0x03, 0xFF])


def test_zoom_tele_sends_expected_bytes(camera, udp_listener):
    camera.zoom(ZoomVelocity(value=1.0))

    packet, _ = udp_listener.recvfrom(64)

    assert packet == bytes([0x81, 0x01, 0x04, 0x07, 0x27, 0xFF])


def test_zoom_wide_sends_expected_bytes(camera, udp_listener):
    camera.zoom(ZoomVelocity(value=-1.0))

    packet, _ = udp_listener.recvfrom(64)

    assert packet == bytes([0x81, 0x01, 0x04, 0x07, 0x37, 0xFF])


def test_zoom_stop_sends_expected_bytes(camera, udp_listener):
    camera.zoom(ZoomVelocity.stop())

    packet, _ = udp_listener.recvfrom(64)

    assert packet == bytes([0x81, 0x01, 0x04, 0x07, 0x00, 0xFF])


def test_recall_preset_sends_expected_bytes(camera, udp_listener):
    camera.recall_preset(5)

    packet, _ = udp_listener.recvfrom(64)

    assert packet == bytes([0x81, 0x01, 0x04, 0x3F, 0x02, 0x05, 0xFF])


def test_save_preset_sends_expected_bytes(camera, udp_listener):
    camera.save_preset(5)

    packet, _ = udp_listener.recvfrom(64)

    assert packet == bytes([0x81, 0x01, 0x04, 0x3F, 0x01, 0x05, 0xFF])


def test_recall_preset_rejects_out_of_range(camera):
    with pytest.raises(ValueError):
        camera.recall_preset(200)


def test_commands_require_connection():
    camera = ViscaOverIpCamera(host="127.0.0.1", port=1259)
    with pytest.raises(PTZCameraError):
        camera.move(PanTiltVelocity.stop())


def test_connect_failure_raises_ptz_camera_error():
    camera = ViscaOverIpCamera(host="256.256.256.256", port=1259)
    with pytest.raises(PTZCameraError):
        camera.connect()
