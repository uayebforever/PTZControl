from .camera import PanTiltVelocity, PTZCamera, PTZCameraError, ZoomVelocity


class MockPTZCamera(PTZCamera):
    """In-memory PTZCamera for development and tests without real hardware.

    Records the last commands it was sent so tests can assert on them.
    """

    def __init__(self) -> None:
        self.connected = False
        self.velocity = PanTiltVelocity.stop()
        self.zoom_velocity = ZoomVelocity.stop()
        self.last_recalled_preset: int | None = None
        self.saved_presets: set[int] = set()

    def connect(self) -> None:
        self.connected = True

    def disconnect(self) -> None:
        self.connected = False

    def move(self, velocity: PanTiltVelocity) -> None:
        self._require_connected()
        self.velocity = velocity

    def zoom(self, velocity: ZoomVelocity) -> None:
        self._require_connected()
        self.zoom_velocity = velocity

    def recall_preset(self, preset_number: int) -> None:
        self._require_connected()
        self.last_recalled_preset = preset_number

    def save_preset(self, preset_number: int) -> None:
        self._require_connected()
        self.saved_presets.add(preset_number)

    def _require_connected(self) -> None:
        if not self.connected:
            raise PTZCameraError("Camera is not connected")
