import subprocess
from unittest.mock import MagicMock

import pytest

from briefcase.exceptions import BriefcaseCommandError, InvalidDeviceError
from briefcase.integrations.android_sdk import ADB


def test_clear_log(mock_sdk, capsys):
    "Invoking `clear_log()` calls `run()` with the appropriate parameters."
    # Mock out the run command on an adb instance
    adb = ADB(mock_sdk, "exampleDevice")
    adb.run = MagicMock(return_value="example normal adb output")

    # Invoke clear_log
    adb.clear_log()

    # Validate call parameters.
    adb.run.assert_called_once_with("logcat", "-c")

    # Validate that the normal output of the command was not printed (since there
    # was no error).
    assert "normal adb output" not in capsys.readouterr()


def test_adb_failure(mock_sdk):
    "If adb logcat fails, the error is caught."
    # Mock out the run command on an adb instance
    adb = ADB(mock_sdk, "exampleDevice")
    adb.run = MagicMock(side_effect=subprocess.CalledProcessError(
        returncode=1, cmd='adb logcat'
    ))

    with pytest.raises(BriefcaseCommandError):
        adb.clear_log()


def test_invalid_device(mock_sdk):
    "If the device doesn't exist, the error is caught."
    # Use real `adb` output from launching an activity that does not exist.
    # Mock out the run command on an adb instance
    adb = ADB(mock_sdk, "exampleDevice")
    adb.run = MagicMock(side_effect=InvalidDeviceError('device', 'exampleDevice'))

    with pytest.raises(InvalidDeviceError):
        adb.clear_log()
