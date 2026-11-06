import logging
from typing import final

from PySide6.QtCore import QTimer
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import (
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ..control.manual_control import DEFAULT_POLL_HZ, ManualControlLoop
from ..input.controller import ControllerNotFoundError, MotionInput, MotionState
from ..input.xbox import XboxController
from ..ptz.camera import PTZCamera, PTZCameraError
from ..ptz.visca import DEFAULT_PORT, ViscaOverIpCamera
from ..video.opencv_source import OpenCvVideoSource
from ..video.source import VideoSource, VideoSourceError
from .motion_display import MotionDisplay
from .video_widget import VideoWidget

log = logging.getLogger(__name__)

VIDEO_REFRESH_HZ = 30.0


@final
class MainWindow(QWidget):
    """Minimal control panel: connect to a camera, then drive it with an Xbox controller.

    Deliberately thin -- this widget only wires user actions to the
    camera/input/control-loop abstractions. It has no tracking or protocol
    logic of its own.
    """

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("PTZ Control")

        self._camera: PTZCamera | None = None
        self._controller: MotionInput | None = None
        self._control_loop: ManualControlLoop | None = None
        self._control_timer: QTimer | None = None
        self._video_source: VideoSource | None = None
        self._video_timer = QTimer(self)
        self._video_timer.setInterval(round(1000 / VIDEO_REFRESH_HZ))
        self._video_timer.timeout.connect(self._on_video_tick)

        self._host_input = QLineEdit("192.168.1.100")
        self._port_input = QLineEdit(str(DEFAULT_PORT))

        self._video_url_input = QLineEdit()
        self._video_url_input.setPlaceholderText("rtsp://192.168.1.100/1 (or device index, e.g. 0)")
        self._video_button = QPushButton("Start Video")
        self._video_button.clicked.connect(self._on_video_clicked)
        self._video_widget = VideoWidget()

        self._connect_button = QPushButton("Connect")
        self._connect_button.clicked.connect(self._on_connect_clicked)

        self._control_button = QPushButton("Start Xbox Control")
        self._control_button.setEnabled(False)
        self._control_button.clicked.connect(self._on_control_clicked)

        self._status_label = QLabel("Disconnected")
        self._motion_display = MotionDisplay()

        form = QFormLayout()
        form.addRow("Camera host", self._host_input)
        form.addRow("Port", self._port_input)
        form.addRow("Video URL", self._video_url_input)

        buttons = QHBoxLayout()
        buttons.addWidget(self._connect_button)
        buttons.addWidget(self._control_button)
        buttons.addWidget(self._video_button)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addLayout(buttons)
        layout.addWidget(self._video_widget, stretch=1)
        layout.addWidget(self._motion_display)
        layout.addWidget(self._status_label)

    def _on_video_clicked(self) -> None:
        if self._video_source is not None:
            self._stop_video()
            return

        text = self._video_url_input.text().strip()
        if not text:
            QMessageBox.warning(self, "No video URL", "Enter a stream URL or device index.")
            return
        source = OpenCvVideoSource(int(text) if text.isdigit() else text)
        try:
            source.open()
        except VideoSourceError as err:
            QMessageBox.critical(self, "Video failed", str(err))
            return

        self._video_source = source
        self._video_timer.start()
        self._video_button.setText("Stop Video")

    def _on_video_tick(self) -> None:
        if self._video_source is not None:
            self._video_widget.set_frame(self._video_source.latest_frame())

    def _stop_video(self) -> None:
        self._video_timer.stop()
        if self._video_source is not None:
            self._video_source.close()
            self._video_source = None
        self._video_widget.set_frame(None)
        self._video_button.setText("Start Video")

    def _on_connect_clicked(self) -> None:
        if self._camera is not None:
            self._disconnect_camera()
            return

        host = self._host_input.text().strip()
        try:
            port = int(self._port_input.text().strip())
        except ValueError:
            QMessageBox.warning(self, "Invalid port", "Port must be a number.")
            return

        camera = ViscaOverIpCamera(host=host, port=port)
        try:
            camera.connect()
        except PTZCameraError as err:
            QMessageBox.critical(self, "Connection failed", str(err))
            return

        self._camera = camera
        self._connect_button.setText("Disconnect")
        self._control_button.setEnabled(True)
        self._status_label.setText(f"Connected to {host}:{port}")

    def _disconnect_camera(self) -> None:
        self._stop_control_loop()
        if self._camera is not None:
            self._camera.disconnect()
            self._camera = None
        self._connect_button.setText("Connect")
        self._control_button.setEnabled(False)
        self._status_label.setText("Disconnected")

    def _on_control_clicked(self) -> None:
        if self._control_loop is not None:
            self._stop_control_loop()
            return

        assert self._camera is not None

        controller = XboxController()
        try:
            controller.open()
        except ControllerNotFoundError as err:
            QMessageBox.critical(self, "Controller not found", str(err))
            return

        self._controller = controller
        self._control_loop = ManualControlLoop(controller, self._camera)

        # Xbox controller polling pumps SDL's OS event queue, which on some
        # platforms (macOS) must happen on the application's main thread.
        # A QTimer ticks the control loop from here -- the Qt main thread --
        # rather than from a background thread.
        timer = QTimer(self)
        timer.setInterval(round(1000 / DEFAULT_POLL_HZ))
        timer.timeout.connect(self._on_control_tick)
        timer.start()
        self._control_timer = timer

        self._control_button.setText("Stop Xbox Control")
        self._status_label.setText("Xbox control active")

    def _on_control_tick(self) -> None:
        assert self._control_loop is not None
        try:
            state = self._control_loop.tick()
            self._motion_display.set_state(state)
        except Exception as err:
            log.exception("Manual control loop failed; stopping.")
            self._stop_control_loop()
            QMessageBox.critical(self, "Controller error", str(err))

    def _stop_control_loop(self) -> None:
        if self._control_timer is not None:
            self._control_timer.stop()
            self._control_timer = None
        if self._control_loop is not None:
            self._control_loop.stop()
            self._control_loop = None
        if self._controller is not None:
            self._controller.close()
            self._controller = None
        self._control_button.setText("Start Xbox Control")
        self._motion_display.set_state(MotionState.neutral())
        if self._camera is not None:
            self._status_label.setText("Connected")

    def closeEvent(self, event: QCloseEvent) -> None:
        self._stop_video()
        self._disconnect_camera()
        super().closeEvent(event)
