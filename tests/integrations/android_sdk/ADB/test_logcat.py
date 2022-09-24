import os
import subprocess
from unittest.mock import MagicMock

import pytest

from briefcase.exceptions import BriefcaseCommandError
from briefcase.integrations.android_sdk import ADB


def test_logcat(mock_tools):
    """Invoking `logcat()` calls `run()` with the appropriate parameters."""
    # Mock out the run command on an adb instance
    adb = ADB(mock_tools, "exampleDevice")

    # Invoke logcat
    adb.logcat("1234")

    # Validate call parameters.
    mock_tools.subprocess.run.assert_called_once_with(
        [
            os.fsdecode(mock_tools.android_sdk.adb_path),
            "-s",
            "exampleDevice",
            "logcat",
            "--pid",
            "1234",
            "EGL_emulation:S",
        ],
        env=mock_tools.android_sdk.env,
        check=True,
        stream_output=True,
    )


def test_adb_failure(mock_tools):
    """If adb logcat fails, the error is caught."""
    # Mock out the run command on an adb instance
    adb = ADB(mock_tools, "exampleDevice")
    mock_tools.subprocess.run = MagicMock(
        side_effect=subprocess.CalledProcessError(returncode=1, cmd="adb logcat")
    )

    with pytest.raises(BriefcaseCommandError):
        adb.logcat("1234")


@pytest.mark.parametrize(
    "return_code",
    (
        0xC000013A,  # Windows: STATUS_CONTROL_C_EXIT in hex
        3221225786,  # Windows: STATUS_CONTROL_C_EXIT in dec
        -2,  # Linux/macOS
    ),
)
def test_adb_ctrl_c(mock_tools, return_code):
    """When the user sends CTRL+C, exit normally."""
    # Mock out the run command on an adb instance
    adb = ADB(mock_tools, "exampleDevice")
    mock_tools.subprocess.run = MagicMock(
        side_effect=subprocess.CalledProcessError(
            returncode=return_code, cmd="adb logcat"
        )
    )

    # does not raise BriefcaseCommandError
    adb.logcat("1234")
