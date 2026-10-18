from abc import ABC, abstractmethod
from dataclasses import dataclass


class ControllerNotFoundError(RuntimeError):
    """Raised when a physical input device cannot be opened."""


@dataclass(frozen=True)
class MotionState:
    """Normalized motion command, produced by a MotionInput on each poll.

    pan:  -1.0 (full left)  .. 1.0 (full right)
    tilt: -1.0 (full down)  .. 1.0 (full up)
    zoom: -1.0 (full wide/out) .. 1.0 (full tele/in)
    preset_recall/preset_save: set to a preset number for one poll when the
    device requests that discrete action, otherwise None.
    """

    pan: float = 0.0
    tilt: float = 0.0
    zoom: float = 0.0
    preset_recall: int | None = None
    preset_save: int | None = None

    @classmethod
    def neutral(cls) -> "MotionState":
        return cls()


class MotionInput(ABC):
    """Abstraction over a device that drives PTZ motion.

    Implementations (an Xbox controller today; a mouse, keyboard, or an
    OpenCV-based tracker later) only need to produce a MotionState when
    polled. Nothing that consumes a MotionInput needs to know what kind of
    device -- or eventually, what kind of algorithm -- is behind it.
    """

    @abstractmethod
    def open(self) -> None:
        """Acquire the device. Raises ControllerNotFoundError if unavailable."""

    @abstractmethod
    def close(self) -> None:
        """Release the device."""

    @abstractmethod
    def poll(self) -> MotionState:
        """Return the current motion state. Called repeatedly by a control loop."""

    def __enter__(self) -> "MotionInput":
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()
