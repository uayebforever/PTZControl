from typing import final

from PySide6.QtCore import QRect, Qt
from PySide6.QtGui import QImage, QPainter
from PySide6.QtWidgets import QWidget

from ..video.source import Frame


@final
class VideoWidget(QWidget):
    """Paints the most recent video frame, scaled to fit with the aspect ratio kept."""

    def __init__(self) -> None:
        super().__init__()
        self.setMinimumSize(320, 180)
        self._image: QImage | None = None
        self._last_sequence = -1

    def set_frame(self, frame: Frame | None) -> None:
        """Show a frame; None clears the display. Repeats of a frame are ignored."""
        if frame is None:
            self._image = None
            self._last_sequence = -1
            self.update()
            return
        if frame.sequence == self._last_sequence:
            return
        self._last_sequence = frame.sequence
        # QImage does not own the buffer, so copy() it before the frame can be reused.
        self._image = QImage(
            frame.image.data, frame.width, frame.height, frame.image.strides[0],
            QImage.Format.Format_BGR888,
        ).copy()
        self.update()

    def paintEvent(self, event) -> None:  # type: ignore[no-untyped-def]
        painter = QPainter(self)
        painter.fillRect(self.rect(), Qt.GlobalColor.black)
        if self._image is not None:
            painter.drawImage(self._target_rect(self._image), self._image)

    def _target_rect(self, image: QImage) -> QRect:
        scaled = image.size().scaled(self.size(), Qt.AspectRatioMode.KeepAspectRatio)
        rect = QRect(0, 0, scaled.width(), scaled.height())
        rect.moveCenter(self.rect().center())
        return rect
