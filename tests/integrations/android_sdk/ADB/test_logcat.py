import subprocess
from unittest.mock import MagicMock

import pytest

from briefcase.exceptions import BriefcaseCommandError
from briefcase.integrations.android_sdk import ADB


def test_logcat(mock_sdk):
    "Invoking `logcat()` calls `run()` with the appropriate parameters."
    # Mock out the run command on an adb instance
    adb = ADB(mock_sdk, "exampleDevice")

    # Invoke logcat
    adb.logcat()

    # Validate call parameters.
    mock_sdk.command.subprocess.run.assert_called_once_with(
        [
            str(mock_sdk.adb_path),
            "-s",
            "exampleDevice",
            "logcat",
            "-s",
            "MainActivity:*",
            "stdio:*",
            "Python:*",
        ],
        env=mock_sdk.env,
        check=True,
    )


def test_adb_failure(mock_sdk):
    "If adb logcat fails, the error is caught."
    # Mock out the run command on an adb instance
    adb = ADB(mock_sdk, "exampleDevice")
    mock_sdk.command.subprocess.run = MagicMock(side_effect=subprocess.CalledProcessError(
        returncode=1, cmd='adb logcat'
    ))

    with pytest.raises(BriefcaseCommandError):
        adb.logcat()
