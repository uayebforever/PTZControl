import time
from collections.abc import Callable
from typing import final

from ..input.controller import MotionInput, MotionState
from ..ptz.camera import PanTiltVelocity, PTZCamera, ZoomVelocity
from .response_curve import PAN_TILT_EXPONENT, ZOOM_EXPONENT, apply_curve
from .speed_ramp import SpeedRamp

DEFAULT_POLL_HZ = 30.0
# Longest time step fed to the speed ramps, so a stalled UI thread does not
# cause one huge jump in speed afterwards.
_MAX_DT = 0.1


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

    def __init__(
        self,
        motion_input: MotionInput,
        camera: PTZCamera,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._motion_input = motion_input
        self._camera = camera
        self._clock = clock
        self._last_time: float | None = None
        self._ramps = {name: SpeedRamp() for name in ("pan", "tilt", "zoom")}
        self._last_pan_tilt = PanTiltVelocity.stop()
        self._last_zoom = ZoomVelocity.stop()

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
        for ramp in self._ramps.values():
            ramp.reset()
        self._last_pan_tilt = PanTiltVelocity.stop()
        self._last_zoom = ZoomVelocity.stop()
        self._camera.stop()

    def _apply(self, state: MotionState) -> None:
        now = self._clock()
        dt = 0.0 if self._last_time is None else min(max(now - self._last_time, 0.0), _MAX_DT)
        self._last_time = now

        pan_tilt = PanTiltVelocity(
            pan=self._ramps["pan"].step(apply_curve(state.pan, PAN_TILT_EXPONENT), dt),
            tilt=self._ramps["tilt"].step(apply_curve(state.tilt, PAN_TILT_EXPONENT), dt),
        )
        zoom = ZoomVelocity(value=self._ramps["zoom"].step(apply_curve(state.zoom, ZOOM_EXPONENT), dt))

        # While moving, pan/tilt is re-sent every tick even if unchanged: the
        # camera backend may alternate between adjacent integer speed steps
        # from one command to the next to approximate fractional speeds.
        if pan_tilt != self._last_pan_tilt or pan_tilt != PanTiltVelocity.stop():
            self._camera.move(pan_tilt)
            self._last_pan_tilt = pan_tilt
        if zoom != self._last_zoom:
            self._camera.zoom(zoom)
            self._last_zoom = zoom
        if state.preset_recall is not None:
            self._camera.recall_preset(state.preset_recall)
        if state.preset_save is not None:
            self._camera.save_preset(state.preset_save)
