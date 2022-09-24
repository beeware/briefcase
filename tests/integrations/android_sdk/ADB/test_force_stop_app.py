import subprocess
from unittest.mock import MagicMock

import pytest

from briefcase.exceptions import BriefcaseCommandError, InvalidDeviceError
from briefcase.integrations.android_sdk import ADB


def test_force_stop_app(mock_tools, capsys):
    """Invoking `force_stop_app()` calls `run()` with the appropriate
    parameters."""
    # Mock out the run command on an adb instance
    adb = ADB(mock_tools, "exampleDevice")
    adb.run = MagicMock(return_value="example normal adb output")

    # Invoke force_stop_app
    adb.force_stop_app("com.example.sample.package")

    # Validate call parameters.
    adb.run.assert_called_once_with(
        "shell", "am", "force-stop", "com.example.sample.package"
    )

    # Validate that the normal output of the command was not printed (since there
    # was no error).
    assert "normal adb output" not in capsys.readouterr()


def test_force_top_fail(mock_tools, capsys):
    """If `force_stop_app()` fails, an error is raised."""
    # Mock out the run command on an adb instance
    adb = ADB(mock_tools, "exampleDevice")
    adb.run = MagicMock(
        side_effect=subprocess.CalledProcessError(returncode=69, cmd="force-stop")
    )

    # Invoke force_stop_app
    with pytest.raises(BriefcaseCommandError):
        adb.force_stop_app("com.example.sample.package")

    # Validate call parameters.
    adb.run.assert_called_once_with(
        "shell", "am", "force-stop", "com.example.sample.package"
    )


def test_invalid_device(mock_tools, capsys):
    """Invoking `force_stop_app()` on an invalid device raises an error."""
    # Mock out the run command on an adb instance
    adb = ADB(mock_tools, "exampleDevice")
    adb.run = MagicMock(side_effect=InvalidDeviceError("device", "exampleDevice"))

    # Invoke force_stop_app
    with pytest.raises(InvalidDeviceError):
        adb.force_stop_app("com.example.sample.package")

    # Validate call parameters.
    adb.run.assert_called_once_with(
        "shell", "am", "force-stop", "com.example.sample.package"
    )
