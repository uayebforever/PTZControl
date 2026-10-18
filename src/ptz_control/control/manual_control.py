import logging
import threading
import time

from ..input.controller import MotionInput, MotionState
from ..ptz.camera import PanTiltVelocity, PTZCamera, ZoomVelocity

log = logging.getLogger(__name__)

_DEFAULT_POLL_HZ = 30.0


class ManualControlLoop:
    """Continuously reads a MotionInput and drives a PTZCamera from it.

    This is the one piece of code in the application that depends on both
    the input abstraction and the camera abstraction. Swapping the Xbox
    controller for a mouse, or later for an OpenCV-based tracker, means
    writing a new MotionInput and pointing an instance of this loop at it
    -- nothing here, in the camera layer, or in the input layer needs to
    change.
    """

    def __init__(
        self,
        motion_input: MotionInput,
        camera: PTZCamera,
        poll_hz: float = _DEFAULT_POLL_HZ,
    ) -> None:
        self._motion_input = motion_input
        self._camera = camera
        self._poll_interval = 1.0 / poll_hz
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._last_state = MotionState.neutral()

    @property
    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def start(self) -> None:
        if self.is_running:
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, name="ManualControlLoop", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=2.0)
            self._thread = None
        self._camera.stop()

    def _run(self) -> None:
        while not self._stop_event.is_set():
            try:
                self._apply(self._motion_input.poll())
            except Exception:
                log.exception("Error in manual control loop; stopping.")
                return
            time.sleep(self._poll_interval)

    def _apply(self, state: MotionState) -> None:
        if state != self._last_state:
            self._camera.move(PanTiltVelocity(pan=state.pan, tilt=state.tilt))
            self._camera.zoom(ZoomVelocity(value=state.zoom))
            self._last_state = state
        if state.preset_recall is not None:
            self._camera.recall_preset(state.preset_recall)
        if state.preset_save is not None:
            self._camera.save_preset(state.preset_save)
