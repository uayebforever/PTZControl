from abc import ABC, abstractmethod
from dataclasses import dataclass
from types import TracebackType

import numpy as np
from numpy.typing import NDArray


class VideoSourceError(RuntimeError):
    """Raised when a video source cannot be opened."""


@dataclass(frozen=True)
class Frame:
    """One decoded video frame.

    image: height x width x 3 uint8 array in BGR channel order (OpenCV's
    native layout, so detectors/trackers can consume it without copying).
    sequence: increases by one for every frame the source decodes, so
    consumers can tell a new frame from one they have already seen.
    """

    image: NDArray[np.uint8]
    sequence: int

    @property
    def width(self) -> int:
        return int(self.image.shape[1])

    @property
    def height(self) -> int:
        return int(self.image.shape[0])


class VideoSource(ABC):
    """Abstraction over a live video feed.

    Consumers (the GUI today; a detector/tracker next) only ever ask for the
    most recent frame and never block on the network or the decoder. A slow
    consumer simply skips frames, which is what a tracker wants: it should
    always work on the freshest picture, never a growing backlog.
    """

    @abstractmethod
    def open(self) -> None:
        """Start the feed. Raises VideoSourceError if it cannot be opened."""

    @abstractmethod
    def close(self) -> None:
        """Stop the feed and release resources."""

    @abstractmethod
    def latest_frame(self) -> Frame | None:
        """Return the newest frame, or None if none has arrived yet."""

    def __enter__(self) -> "VideoSource":
        self.open()
        return self

    def __exit__(
            self,
            type_: type[BaseException] | None,
            value: BaseException | None,
            traceback: TracebackType | None,
    ) -> bool | None:
        self.close()
