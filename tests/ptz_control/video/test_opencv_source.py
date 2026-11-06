import time
from typing import Any

import numpy as np
import pytest

from ptz_control.video.opencv_source import OpenCvVideoSource
from ptz_control.video.source import VideoSourceError


class FakeCapture:
    def __init__(self, opened: bool = True) -> None:
        self._opened = opened
        self.released = False
        self._count = 0

    def isOpened(self) -> bool:
        return self._opened

    def read(self) -> tuple[bool, Any]:
        time.sleep(0.001)
        self._count += 1
        return True, np.full((4, 6, 3), self._count % 255, dtype=np.uint8)

    def release(self) -> None:
        self.released = True


def _wait_for_frame(source: OpenCvVideoSource):
    deadline = time.monotonic() + 2.0
    while time.monotonic() < deadline:
        frame = source.latest_frame()
        if frame is not None:
            return frame
        time.sleep(0.005)
    raise AssertionError("no frame arrived")


def test_open_raises_when_capture_cannot_open() -> None:
    capture = FakeCapture(opened=False)
    source = OpenCvVideoSource("rtsp://x", capture_factory=lambda _: capture)
    with pytest.raises(VideoSourceError):
        source.open()
    assert capture.released


def test_latest_frame_is_none_before_open() -> None:
    assert OpenCvVideoSource(0, capture_factory=lambda _: FakeCapture()).latest_frame() is None


def test_delivers_frames_with_increasing_sequence_and_dimensions() -> None:
    with OpenCvVideoSource(0, capture_factory=lambda _: FakeCapture()) as source:
        first = _wait_for_frame(source)
        assert (first.width, first.height) == (6, 4)
        time.sleep(0.05)
        assert source.latest_frame().sequence > first.sequence  # type: ignore[union-attr]


def test_close_releases_capture_and_clears_frame() -> None:
    capture = FakeCapture()
    source = OpenCvVideoSource(0, capture_factory=lambda _: capture)
    source.open()
    _wait_for_frame(source)
    source.close()
    assert capture.released
    assert source.latest_frame() is None
