from pytest_mock import MockerFixture

from ptz_control.input.xbox import XboxController


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
    controller, _ = make_controller(mocker, {2: -1.0, 5: -1.0})
    assert controller.poll().zoom == 0.0


def test_untouched_triggers_reporting_zero_give_no_zoom(mocker: MockerFixture) -> None:
    controller, _ = make_controller(mocker, {2: 0.0, 5: 0.0})
    assert controller.poll().zoom == 0.0


def test_trigger_press_zooms_in_and_out(mocker: MockerFixture) -> None:
    controller, joystick = make_controller(mocker, {2: -1.0, 5: 1.0})
    assert controller.poll().zoom == 1.0
    joystick.axes = {2: 1.0, 5: -1.0}
    assert controller.poll().zoom == -1.0


def test_zero_is_real_half_press_once_axis_has_moved(mocker: MockerFixture) -> None:
    controller, joystick = make_controller(mocker, {2: -1.0, 5: -1.0})
    controller.poll()
    joystick.axes = {2: -1.0, 5: 0.0}
    assert controller.poll().zoom == 0.5
