import subprocess
from pathlib import Path

import pytest

from briefcase.exceptions import BriefcaseCommandError


def devices_result(name):
    """Load a adb devices result file from the sample directory, and return the
    content."""
    adb_samples = Path(__file__).parent / "devices"
    with (adb_samples / (name + ".out")).open(encoding="utf-8") as adb_output_file:
        return adb_output_file.read()


def test_no_devices(mock_sdk):
    """If there are no devices, an empty list is returned."""
    mock_sdk.command.subprocess.check_output.return_value = devices_result("no_devices")

    assert mock_sdk.devices() == {}


def test_one_emulator(mock_sdk):
    """If there is a single emulator, it is returned."""
    mock_sdk.command.subprocess.check_output.return_value = devices_result(
        "one_emulator"
    )

    assert mock_sdk.devices() == {
        "emulator-5554": {
            "name": "Android SDK built for x86",
            "authorized": True,
        },
    }


def test_multiple_devices(mock_sdk):
    """If there are multiple devices, they are all returned."""
    mock_sdk.command.subprocess.check_output.return_value = devices_result(
        "multiple_devices"
    )

    assert mock_sdk.devices() == {
        "041234567892009a": {
            "name": "Unknown device (not authorized for development)",
            "authorized": False,
        },
        "KABCDABCDA1513": {
            "name": "Kogan Agora 9",
            "authorized": True,
        },
        "emulator-5554": {
            "name": "Android SDK built for x86",
            "authorized": True,
        },
        "emulator-5556": {
            "name": "Unknown device (offline)",
            "authorized": False,
        },
    }


def test_adb_error(mock_sdk):
    """If there is a problem invoking adb, an error is returned."""
    mock_sdk.command.subprocess.check_output.side_effect = (
        subprocess.CalledProcessError(returncode=69, cmd="adb devices -l")
    )

    with pytest.raises(BriefcaseCommandError):
        mock_sdk.devices()


def test_daemon_start(mock_sdk):
    """If ADB outputs the daemon startup message, ignore those messages."""
    mock_sdk.command.subprocess.check_output.return_value = devices_result(
        "daemon_start"
    )

    assert mock_sdk.devices() == {}
