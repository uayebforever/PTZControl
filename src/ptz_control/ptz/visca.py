import logging
import socket
from typing import final

from .camera import PanTiltVelocity, PTZCamera, PTZCameraError, ZoomVelocity

log = logging.getLogger(__name__)

# PTZOptics cameras speak "raw" VISCA over IP: plain VISCA command bytes
# (the same bytes used over a serial link), terminated with 0xFF, sent
# directly as a UDP datagram -- no extra framing/sequence-number header.
# This differs from the 8-byte "encapsulated" VISCA-over-IP header used by
# some other manufacturers (e.g. Sony).
DEFAULT_PORT = 1259
DEFAULT_CAMERA_ADDRESS = 1

_TERMINATOR = 0xFF

_MIN_PAN_SPEED, _MAX_PAN_SPEED = 0x01, 0x18
_MIN_TILT_SPEED, _MAX_TILT_SPEED = 0x01, 0x14
_MAX_ZOOM_SPEED = 0x07

# The camera only accepts whole speed steps. When True, a fractional target
# speed (e.g. 1.4) is approximated by alternating between the neighbouring
# steps (1 and 2) in proportion, via error diffusion, across successive
# move() commands. Set False for plain rounding.
DITHER_SPEED_STEPS = True

_PAN_STOP, _PAN_LEFT, _PAN_RIGHT = 0x03, 0x01, 0x02
_TILT_STOP, _TILT_UP, _TILT_DOWN = 0x03, 0x01, 0x02

_MIN_PRESET_NUMBER, _MAX_PRESET_NUMBER = 0, 127


@final
class ViscaOverIpCamera(PTZCamera):
    """PTZ camera backend for PTZOptics-style VISCA-over-IP (UDP)."""

    def __init__(
        self,
        host: str,
        port: int = DEFAULT_PORT,
        camera_address: int = DEFAULT_CAMERA_ADDRESS,
    ) -> None:
        self._host = host
        self._port = port
        self._address_byte = 0x80 | camera_address
        self._socket: socket.socket | None = None
        self._pan_dither = _Dither(DITHER_SPEED_STEPS)
        self._tilt_dither = _Dither(DITHER_SPEED_STEPS)

    def connect(self) -> None:
        if self._socket is not None:
            return
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            sock.connect((self._host, self._port))
        except OSError as err:
            sock.close()
            raise PTZCameraError(f"Could not reach camera at {self._host}:{self._port}: {err}") from err
        self._socket = sock
        log.info("Connected to VISCA-over-IP camera at %s:%d", self._host, self._port)

    def disconnect(self) -> None:
        if self._socket is not None:
            self._socket.close()
            self._socket = None

    def move(self, velocity: PanTiltVelocity) -> None:
        pan_speed, pan_direction = _axis_speed_and_direction(
            velocity.pan, _MIN_PAN_SPEED, _MAX_PAN_SPEED, _PAN_LEFT, _PAN_RIGHT, _PAN_STOP, self._pan_dither
        )
        tilt_speed, tilt_direction = _axis_speed_and_direction(
            velocity.tilt, _MIN_TILT_SPEED, _MAX_TILT_SPEED, _TILT_DOWN, _TILT_UP, _TILT_STOP, self._tilt_dither
        )
        self._send(0x01, 0x06, 0x01, pan_speed, tilt_speed, pan_direction, tilt_direction)

    def zoom(self, velocity: ZoomVelocity) -> None:
        if velocity.value == 0.0:
            self._send(0x01, 0x04, 0x07, 0x00)
            return
        speed = max(1, round(abs(velocity.value) * _MAX_ZOOM_SPEED))
        mode = 0x20 if velocity.value > 0 else 0x30  # tele (zoom in) vs wide (zoom out)
        self._send(0x01, 0x04, 0x07, mode | speed)

    def recall_preset(self, preset_number: int) -> None:
        self._send(0x01, 0x04, 0x3F, 0x02, _validated_preset(preset_number))

    def save_preset(self, preset_number: int) -> None:
        self._send(0x01, 0x04, 0x3F, 0x01, _validated_preset(preset_number))

    def _send(self, *payload: int) -> None:
        if self._socket is None:
            raise PTZCameraError("Camera is not connected")
        packet = bytes([self._address_byte, *payload, _TERMINATOR])
        try:
            self._socket.send(packet)
        except OSError as err:
            raise PTZCameraError(f"Failed to send VISCA command to {self._host}:{self._port}: {err}") from err


class _Dither:
    """First-order error diffusion from fractional to whole speed steps."""

    def __init__(self, enabled: bool) -> None:
        self._enabled = enabled
        self._error = 0.0

    def quantize(self, fractional: float) -> int:
        if not self._enabled:
            return round(fractional)
        wanted = fractional + self._error
        chosen = round(wanted)
        self._error = wanted - chosen
        return chosen

    def reset(self) -> None:
        self._error = 0.0


def _axis_speed_and_direction(
    value: float,
    min_speed: int,
    max_speed: int,
    negative_code: int,
    positive_code: int,
    stop_code: int,
    dither: _Dither | None = None,
) -> tuple[int, int]:
    if value == 0.0:
        if dither is not None:
            dither.reset()
        return min_speed, stop_code
    fractional = min_speed + abs(value) * (max_speed - min_speed)
    speed = dither.quantize(fractional) if dither is not None else round(fractional)
    speed = max(min_speed, min(max_speed, speed))
    direction = positive_code if value > 0 else negative_code
    return speed, direction


def _validated_preset(preset_number: int) -> int:
    if not (_MIN_PRESET_NUMBER <= preset_number <= _MAX_PRESET_NUMBER):
        raise ValueError(
            f"preset_number must be in [{_MIN_PRESET_NUMBER}, {_MAX_PRESET_NUMBER}], got {preset_number}"
        )
    return preset_number
