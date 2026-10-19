from ptz_control.input.controller import MotionState


def test_neutral_state_has_no_motion_or_presets():
    state = MotionState.neutral()

    assert state.pan == 0.0
    assert state.tilt == 0.0
    assert state.zoom == 0.0
    assert state.preset_recall is None
    assert state.preset_save is None
