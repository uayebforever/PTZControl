from typing import final, override

from PySide6.QtCore import QPointF, QRectF, QSize, Qt
from PySide6.QtGui import QColor, QPaintEvent, QPainter, QPalette, QPen
from PySide6.QtWidgets import QSizePolicy, QWidget

from ..input.controller import MotionState
from .geometry import clamp_to_unit_disc


@final
class MotionDisplay(QWidget):
    """Live view of a MotionState: a joystick dot for pan/tilt, a bar for zoom."""

    _STICK_SIZE = 140
    _ZOOM_WIDTH = 24
    _GAP = 20

    def __init__(self) -> None:
        super().__init__()
        self._state = MotionState.neutral()
        self.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)

    def set_state(self, state: MotionState) -> None:
        if state != self._state:
            self._state = state
            self.update()

    @override
    def sizeHint(self) -> QSize:
        return QSize(self._STICK_SIZE + self._GAP + self._ZOOM_WIDTH + 8, self._STICK_SIZE + 8)

    @override
    def minimumSizeHint(self) -> QSize:
        return self.sizeHint()

    @override
    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        palette = self.palette()
        outline = QPen(palette.color(QPalette.ColorRole.Mid), 1.5)
        accent = palette.color(QPalette.ColorRole.Highlight)
        total_w = self._STICK_SIZE + self._GAP + self._ZOOM_WIDTH
        left = (self.width() - total_w) / 2
        top = (self.height() - self._STICK_SIZE) / 2

        self._paint_stick(painter, QRectF(left, top, self._STICK_SIZE, self._STICK_SIZE), outline, accent)
        zoom_rect = QRectF(left + self._STICK_SIZE + self._GAP, top, self._ZOOM_WIDTH, self._STICK_SIZE)
        self._paint_zoom(painter, zoom_rect, outline, accent)

    def _paint_stick(self, painter: QPainter, rect: QRectF, outline: QPen, accent: QColor) -> None:
        painter.setPen(outline)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(rect)
        centre = rect.center()
        painter.drawLine(QPointF(rect.left(), centre.y()), QPointF(rect.right(), centre.y()))
        painter.drawLine(QPointF(centre.x(), rect.top()), QPointF(centre.x(), rect.bottom()))

        x, y = clamp_to_unit_disc(self._state.pan, self._state.tilt)
        radius = rect.width() / 2
        dot_radius = 8.0
        travel = radius - dot_radius
        # Screen y grows downward; positive tilt is up.
        dot = QPointF(centre.x() + x * travel, centre.y() - y * travel)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(accent)
        painter.drawEllipse(dot, dot_radius, dot_radius)

    def _paint_zoom(self, painter: QPainter, rect: QRectF, outline: QPen, accent: QColor) -> None:
        painter.setPen(outline)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(rect, 4, 4)
        mid = rect.center().y()
        painter.drawLine(QPointF(rect.left(), mid), QPointF(rect.right(), mid))

        zoom = max(-1.0, min(1.0, self._state.zoom))
        extent = zoom * rect.height() / 2
        # Positive zoom (tele/in) fills upward from the midline; negative fills downward.
        fill = QRectF(rect.left(), mid - max(extent, 0.0), rect.width(), abs(extent))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(accent)
        painter.drawRect(fill)
