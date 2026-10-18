from abc import ABC, abstractmethod
from dataclasses import dataclass


class PTZCameraError(RuntimeError):
    """Raised when a PTZ camera command fails or the camera is unreachable."""


@dataclass(frozen=True)
class PanTiltVelocity:
    """Normalized pan/tilt velocity.

    pan:  -1.0 (full left)  .. 1.0 (full right)
    tilt: -1.0 (full down)  .. 1.0 (full up)
    """

    pan: float
    tilt: float

    def __post_init__(self) -> None:
        _require_unit_range("pan", self.pan)
        _require_unit_range("tilt", self.tilt)

    @classmethod
    def stop(cls) -> "PanTiltVelocity":
        return cls(pan=0.0, tilt=0.0)


@dataclass(frozen=True)
class ZoomVelocity:
    """Normalized zoom velocity: -1.0 (full wide/out) .. 1.0 (full tele/in)."""

    value: float

    def __post_init__(self) -> None:
        _require_unit_range("zoom", self.value)

    @classmethod
    def stop(cls) -> "ZoomVelocity":
        return cls(value=0.0)


def _require_unit_range(name: str, value: float) -> None:
    if not (-1.0 <= value <= 1.0):
        raise ValueError(f"{name} must be in [-1.0, 1.0], got {value}")


class PTZCamera(ABC):
    """Abstraction over a pan/tilt/zoom camera.

    Each implementation translates these normalized, protocol-agnostic
    commands into whatever a specific camera actually speaks (VISCA over
    IP, ONVIF, ...). Nothing outside this package -- manual joystick
    control today, an OpenCV tracker later -- should depend on anything
    but this interface.
    """

    @abstractmethod
    def connect(self) -> None:
        """Establish any connection/session needed before sending commands."""

    @abstractmethod
    def disconnect(self) -> None:
        """Release any connection/session resources."""

    @abstractmethod
    def move(self, velocity: PanTiltVelocity) -> None:
        """Start continuous pan/tilt motion at the given normalized velocity."""

    @abstractmethod
    def zoom(self, velocity: ZoomVelocity) -> None:
        """Start continuous zoom motion at the given normalized velocity."""

    def stop(self) -> None:
        """Stop all pan/tilt/zoom motion."""
        self.move(PanTiltVelocity.stop())
        self.zoom(ZoomVelocity.stop())

    @abstractmethod
    def recall_preset(self, preset_number: int) -> None:
        """Move the camera to a previously stored preset position."""

    @abstractmethod
    def save_preset(self, preset_number: int) -> None:
        """Store the camera's current position as a preset."""

    def __enter__(self) -> "PTZCamera":
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.disconnect()
