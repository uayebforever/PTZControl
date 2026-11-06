from ptz_control.cli.cli_main import _parse_args


def test_camera_host_defaults_to_none() -> None:
    assert _parse_args([]).camera_host is None


def test_camera_host_option() -> None:
    assert _parse_args(["--camera-host", "10.0.0.5"]).camera_host == "10.0.0.5"


def test_camera_ip_alias() -> None:
    assert _parse_args(["--camera-ip", "10.0.0.5"]).camera_host == "10.0.0.5"
