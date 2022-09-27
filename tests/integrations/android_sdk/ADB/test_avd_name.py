import subprocess
from unittest.mock import MagicMock

import pytest

from briefcase.exceptions import BriefcaseCommandError, InvalidDeviceError
from briefcase.integrations.android_sdk import ADB


def test_emulator(mock_tools, capsys):
    """Invoking `avd_name()` on an emulator returns the AVD."""
    # Mock out the adb response for an emulator
    adb = ADB(mock_tools, "deafbeefcafe")
    adb.run = MagicMock(return_value="exampledevice\nOK\n")

    # Invoke avd_name
    assert adb.avd_name() == "exampledevice"

    # Validate call parameters.
    adb.run.assert_called_once_with("emu", "avd", "name")


def test_device(mock_tools, capsys):
    """Invoking `avd_name()` on a device returns None."""
    # Mock out the adb response for a physical device
    adb = ADB(mock_tools, "deafbeefcafe")
    adb.run = MagicMock(
        side_effect=subprocess.CalledProcessError(returncode=1, cmd="emu avd name")
    )

    # Invoke avd_name
    assert adb.avd_name() is None

    # Validate call parameters.
    adb.run.assert_called_once_with("emu", "avd", "name")


def test_adb_failure(mock_tools, capsys):
    """If `adb()` fails for a miscellaneous reason, an error is raised."""
    # Mock out the run command on an adb instance
    adb = ADB(mock_tools, "exampleDevice")
    adb.run = MagicMock(
        side_effect=subprocess.CalledProcessError(returncode=69, cmd="emu avd name")
    )

    # Invoke install
    with pytest.raises(BriefcaseCommandError):
        adb.avd_name()

    # Validate call parameters.
    adb.run.assert_called_once_with("emu", "avd", "name")


def test_invalid_device(mock_tools, capsys):
    """Invoking `avd_name()` on an invalid device raises an error."""
    # Mock out the run command on an adb instance
    adb = ADB(mock_tools, "exampleDevice")
    adb.run = MagicMock(side_effect=InvalidDeviceError("device", "exampleDevice"))

    # Invoke install
    with pytest.raises(InvalidDeviceError):
        adb.avd_name()

    # Validate call parameters.
    adb.run.assert_called_once_with("emu", "avd", "name")
