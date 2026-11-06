from pytest_mock import MockerFixture

from ptz_control.input.xbox import _AXIS_LEFT_TRIGGER, _AXIS_RIGHT_TRIGGER, XboxController

LT = _AXIS_LEFT_TRIGGER
RT = _AXIS_RIGHT_TRIGGER


class FakeJoystick:
    def __init__(self, axes: dict[int, float]) -> None:
        self.axes = axes

    def get_axis(self, index: int) -> float:
        return self.axes.get(index, 0.0)


def make_controller(mocker: MockerFixture, axes: dict[int, float]) -> tuple[XboxController, FakeJoystick]:
    mocker.patch("pygame.event.pump")
    joystick = FakeJoystick(axes)
    controller = XboxController()
    controller._joystick = joystick  # pyright: ignore
    return controller, joystick


def test_released_triggers_at_minus_one_give_no_zoom(mocker: MockerFixture) -> None:
    controller, _ = make_controller(mocker, {LT: -1.0, RT: -1.0})
    assert controller.poll().zoom == 0.0


def test_untouched_triggers_reporting_zero_give_no_zoom(mocker: MockerFixture) -> None:
    controller, _ = make_controller(mocker, {LT: 0.0, RT: 0.0})
    assert controller.poll().zoom == 0.0


def test_trigger_press_zooms_in_and_out(mocker: MockerFixture) -> None:
    controller, joystick = make_controller(mocker, {LT: -1.0, RT: 1.0})
    assert controller.poll().zoom == 1.0
    joystick.axes = {LT: 1.0, RT: -1.0}
    assert controller.poll().zoom == -1.0


def test_zero_is_real_half_press_once_axis_has_moved(mocker: MockerFixture) -> None:
    controller, joystick = make_controller(mocker, {LT: -1.0, RT: -1.0})
    controller.poll()
    joystick.axes = {LT: -1.0, RT: 0.0}
    assert controller.poll().zoom == 0.5


def test_right_stick_axis_is_not_read_as_a_trigger(mocker: MockerFixture) -> None:
    # Axis 2 is the right stick X on Windows/macOS; a small deflection there
    # must not produce zoom.
    controller, _ = make_controller(mocker, {LT: -1.0, RT: -1.0, 2: 0.02, 3: 0.03})
    assert controller.poll().zoom == 0.0
