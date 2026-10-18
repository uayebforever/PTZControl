from ..input.controller import MotionInput, MotionState
from ..ptz.camera import PanTiltVelocity, PTZCamera, ZoomVelocity

DEFAULT_POLL_HZ = 30.0


class ManualControlLoop:
    """Polls a MotionInput once per tick() and drives a PTZCamera from it.

    This is the one piece of code in the application that depends on both
    the input abstraction and the camera abstraction. Swapping the Xbox
    controller for a mouse, or later for an OpenCV-based tracker, means
    writing a new MotionInput and pointing an instance of this loop at it
    -- nothing here, in the camera layer, or in the input layer needs to
    change.

    This class does not schedule itself: call tick() repeatedly from
    whatever timer or loop the host application uses, on the same thread
    that opened the MotionInput (see MotionInput for why that matters).
    Scheduling is a platform/runtime concern that belongs to the caller,
    not to this glue logic.
    """

    def __init__(self, motion_input: MotionInput, camera: PTZCamera) -> None:
        self._motion_input = motion_input
        self._camera = camera
        self._last_state = MotionState.neutral()

    def tick(self) -> None:
        """Poll the motion input once and apply the result to the camera."""
        self._apply(self._motion_input.poll())

    def stop(self) -> None:
        """Stop all camera motion. Call once the caller has stopped ticking."""
        self._camera.stop()

    def _apply(self, state: MotionState) -> None:
        if state != self._last_state:
            self._camera.move(PanTiltVelocity(pan=state.pan, tilt=state.tilt))
            self._camera.zoom(ZoomVelocity(value=state.zoom))
            self._last_state = state
        if state.preset_recall is not None:
            self._camera.recall_preset(state.preset_recall)
        if state.preset_save is not None:
            self._camera.save_preset(state.preset_save)
