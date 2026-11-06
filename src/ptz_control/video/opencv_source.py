import logging
import threading
from typing import Any, Callable, final

import cv2

from .source import Frame, VideoSource, VideoSourceError

log = logging.getLogger(__name__)

# Seconds to wait between retries when the stream drops or a read fails.
_RETRY_DELAY_S = 0.2


def _default_capture(location: str | int) -> Any:
    return cv2.VideoCapture(location)  # pyright: ignore[reportAny]


@final
class OpenCvVideoSource(VideoSource):
    """Reads an RTSP/HTTP URL, file, or local device index with cv2.VideoCapture.

    Decoding runs on a background thread that overwrites a single "latest
    frame" slot, so latest_frame() is instant and the Qt main thread is
    never blocked by network jitter or decoding.
    """

    def __init__(
            self,
            location: str | int,
            capture_factory: Callable[[str | int], Any] = _default_capture,
    ) -> None:
        self._location = location
        self._capture_factory = capture_factory
        self._capture: Any = None
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()
        self._lock = threading.Lock()
        self._latest: Frame | None = None
        self._sequence = 0

    def open(self) -> None:
        if self._thread is not None:
            return
        capture = self._capture_factory(self._location)
        if not capture.isOpened():
            capture.release()
            raise VideoSourceError(f"Could not open video source: {self._location}")
        self._capture = capture
        self._stop.clear()
        self._latest = None
        self._thread = threading.Thread(target=self._read_loop, name="video-capture", daemon=True)
        self._thread.start()

    def close(self) -> None:
        thread, self._thread = self._thread, None
        if thread is None:
            return
        self._stop.set()
        thread.join(timeout=5.0)
        if self._capture is not None:
            self._capture.release()
            self._capture = None
        self._latest = None

    def latest_frame(self) -> Frame | None:
        with self._lock:
            return self._latest

    def _read_loop(self) -> None:
        capture = self._capture
        while not self._stop.is_set():
            ok, image = capture.read()
            if not ok or image is None:
                log.debug("Video read failed; retrying.")
                self._stop.wait(_RETRY_DELAY_S)
                continue
            self._sequence += 1
            frame = Frame(image=image, sequence=self._sequence)
            with self._lock:
                self._latest = frame
