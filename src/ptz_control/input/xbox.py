import logging

import pygame

from .controller import ControllerNotFoundError, MotionInput, MotionState

log = logging.getLogger(__name__)

# SDL's standard Xbox controller axis layout (consistent across the
# Windows/Mac/Linux backends pygame uses).
_AXIS_LEFT_STICK_X = 0
_AXIS_LEFT_STICK_Y = 1
_AXIS_LEFT_TRIGGER = 2
_AXIS_RIGHT_TRIGGER = 5

_DEFAULT_DEADZONE = 0.15


class XboxController(MotionInput):
    """MotionInput driven by an Xbox controller via pygame's joystick API.

    Left stick drives pan/tilt. Triggers drive zoom: right trigger zooms
    in (tele), left trigger zooms out (wide). Preset buttons are not yet
    wired up -- preset_recall/preset_save are always None for now.
    """

    def __init__(self, joystick_index: int = 0, deadzone: float = _DEFAULT_DEADZONE) -> None:
        self._joystick_index = joystick_index
        self._deadzone = deadzone
        self._joystick: pygame.joystick.JoystickType | None = None

    def open(self) -> None:
        if not pygame.get_init():
            pygame.init()
        pygame.joystick.init()
        if self._joystick_index >= pygame.joystick.get_count():
            raise ControllerNotFoundError(f"No controller found at index {self._joystick_index}")
        joystick = pygame.joystick.Joystick(self._joystick_index)
        joystick.init()
        self._joystick = joystick
        log.info("Opened controller: %s", joystick.get_name())

    def close(self) -> None:
        if self._joystick is not None:
            self._joystick.quit()
            self._joystick = None

    def poll(self) -> MotionState:
        if self._joystick is None:
            raise ControllerNotFoundError("Controller is not open")

        pygame.event.pump()

        pan = self._apply_deadzone(self._joystick.get_axis(_AXIS_LEFT_STICK_X))
        # SDL reports the Y axis as positive-down; flip so pushing the stick
        # up produces positive tilt, matching MotionState's convention.
        tilt = -self._apply_deadzone(self._joystick.get_axis(_AXIS_LEFT_STICK_Y))

        zoom_in = self._normalize_trigger(self._joystick.get_axis(_AXIS_RIGHT_TRIGGER))
        zoom_out = self._normalize_trigger(self._joystick.get_axis(_AXIS_LEFT_TRIGGER))

        return MotionState(pan=pan, tilt=tilt, zoom=zoom_in - zoom_out)

    def _apply_deadzone(self, value: float) -> float:
        if abs(value) < self._deadzone:
            return 0.0
        sign = 1.0 if value > 0 else -1.0
        return sign * (abs(value) - self._deadzone) / (1.0 - self._deadzone)

    @staticmethod
    def _normalize_trigger(value: float) -> float:
        # SDL reports triggers in [-1.0 (released), 1.0 (fully pressed)].
        return max(0.0, (value + 1.0) / 2.0)
