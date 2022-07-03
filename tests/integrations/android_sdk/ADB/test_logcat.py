import os
import subprocess
from unittest.mock import MagicMock

import pytest

from briefcase.exceptions import BriefcaseCommandError
from briefcase.integrations.android_sdk import ADB


def test_logcat(mock_sdk):
    """Invoking `logcat()` calls `run()` with the appropriate parameters."""
    # Mock out the run command on an adb instance
    adb = ADB(mock_sdk, "exampleDevice")

    # Invoke logcat
    adb.logcat()

    # Validate call parameters.
    mock_sdk.command.subprocess.run.assert_called_once_with(
        [
            os.fsdecode(mock_sdk.adb_path),
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
        stream_output=True,
    )


def test_adb_failure(mock_sdk):
    """If adb logcat fails, the error is caught."""
    # Mock out the run command on an adb instance
    adb = ADB(mock_sdk, "exampleDevice")
    mock_sdk.command.subprocess.run = MagicMock(
        side_effect=subprocess.CalledProcessError(returncode=1, cmd="adb logcat")
    )

    with pytest.raises(BriefcaseCommandError):
        adb.logcat()


@pytest.mark.parametrize(
    "return_code",
    (
        0xC000013A,  # Windows: STATUS_CONTROL_C_EXIT in hex
        3221225786,  # Windows: STATUS_CONTROL_C_EXIT in dec
        -2,  # Linux/macOS
    ),
)
def test_adb_ctrl_c(mock_sdk, return_code):
    """When the user sends CTRL+C, exit normally."""
    # Mock out the run command on an adb instance
    adb = ADB(mock_sdk, "exampleDevice")
    mock_sdk.command.subprocess.run = MagicMock(
        side_effect=subprocess.CalledProcessError(
            returncode=return_code, cmd="adb logcat"
        )
    )

    # does not raise BriefcaseCommandError
    adb.logcat()
