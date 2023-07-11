import subprocess
from unittest.mock import MagicMock

import pytest

from briefcase.exceptions import BriefcaseCommandError, InvalidDeviceError


def test_install_apk(adb, capsys):
    """Invoking `install_apk()` calls `run()` with the appropriate parameters."""
    # Mock out the run command on an adb instance
    adb.run = MagicMock(return_value="example normal adb output")

    # Invoke install
    adb.install_apk("example.apk")

    # Validate call parameters.
    adb.run.assert_called_once_with("install", "-r", "example.apk")

    # Validate that the normal output of the command was not printed (since there
    # was no error).
    assert "normal adb output" not in capsys.readouterr()


def test_install_failure(adb, capsys):
    """If `install_apk()` fails, an error is raised."""
    # Mock out the run command on an adb instance
    adb.run = MagicMock(
        side_effect=subprocess.CalledProcessError(returncode=2, cmd="install")
    )

    # Invoke install
    with pytest.raises(BriefcaseCommandError):
        adb.install_apk("example.apk")

    # Validate call parameters.
    adb.run.assert_called_once_with("install", "-r", "example.apk")


def test_invalid_device(adb, capsys):
    """Invoking `install_apk()` on an invalid device raises an error."""
    # Mock out the run command on an adb instance
    adb.run = MagicMock(side_effect=InvalidDeviceError("device", "exampleDevice"))

    # Invoke install
    with pytest.raises(InvalidDeviceError):
        adb.install_apk("example.apk")

    # Validate call parameters.
    adb.run.assert_called_once_with("install", "-r", "example.apk")
