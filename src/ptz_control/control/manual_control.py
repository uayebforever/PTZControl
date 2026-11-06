from typing import final

from ..input.controller import MotionInput, MotionState
from ..ptz.camera import PanTiltVelocity, PTZCamera, ZoomVelocity
from .response_curve import PAN_TILT_EXPONENT, ZOOM_EXPONENT, apply_curve

DEFAULT_POLL_HZ = 30.0


@final
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

    def tick(self) -> MotionState:
        """Poll the motion input once, apply it to the camera, and return it.

        The returned state is the raw (unshaped) controller position; the
        response curve in response_curve.py is applied only to what is sent
        to the camera.
        """
        state = self._motion_input.poll()
        self._apply(state)
        return state

    def stop(self) -> None:
        """Stop all camera motion. Call once the caller has stopped ticking."""
        self._camera.stop()

    def _apply(self, state: MotionState) -> None:
        if state != self._last_state:
            self._camera.move(
                PanTiltVelocity(
                    pan=apply_curve(state.pan, PAN_TILT_EXPONENT),
                    tilt=apply_curve(state.tilt, PAN_TILT_EXPONENT),
                )
            )
            self._camera.zoom(ZoomVelocity(value=apply_curve(state.zoom, ZOOM_EXPONENT)))
            self._last_state = state
        if state.preset_recall is not None:
            self._camera.recall_preset(state.preset_recall)
        if state.preset_save is not None:
            self._camera.save_preset(state.preset_save)
