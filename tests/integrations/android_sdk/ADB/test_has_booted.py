import subprocess
from unittest.mock import MagicMock

import pytest

from briefcase.exceptions import BriefcaseCommandError, InvalidDeviceError


def test_booted(adb, capsys):
    """A booted device returns true."""
    # Mock out the adb response for an emulator
    adb.run = MagicMock(return_value="1\n")

    # Invoke avd_name
    assert adb.has_booted()

    # Validate call parameters.
    adb.run.assert_called_once_with("shell", "getprop", "sys.boot_completed")


def test_not_booted(adb, capsys):
    """A non-booted device returns False."""
    # Mock out the adb response for an emulator
    adb.run = MagicMock(return_value="\n")

    # Invoke avd_name
    assert not adb.has_booted()

    # Validate call parameters.
    adb.run.assert_called_once_with("shell", "getprop", "sys.boot_completed")


def test_adb_failure(adb, capsys):
    """If ADB fails, an error is raised."""
    # Mock out the adb response for an emulator
    adb.run = MagicMock(
        side_effect=subprocess.CalledProcessError(returncode=69, cmd="emu avd name")
    )

    # Invoke avd_name
    with pytest.raises(BriefcaseCommandError):
        adb.has_booted()

    # Validate call parameters.
    adb.run.assert_called_once_with("shell", "getprop", "sys.boot_completed")


def test_invalid_device(adb, capsys):
    """If the device ID is invalid, an error is raised."""
    # Mock out the adb response for an emulator
    adb.run = MagicMock(side_effect=InvalidDeviceError("device", "exampleDevice"))

    # Invoke avd_name
    with pytest.raises(BriefcaseCommandError):
        adb.has_booted()

    # Validate call parameters.
    adb.run.assert_called_once_with("shell", "getprop", "sys.boot_completed")
