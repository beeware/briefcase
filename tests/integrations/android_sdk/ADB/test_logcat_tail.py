import os
import subprocess
from datetime import datetime
from unittest.mock import MagicMock

import pytest

from briefcase.exceptions import BriefcaseCommandError
from briefcase.integrations.android_sdk import ADB


def test_logcat_tail(mock_tools):
    """Invoking `logcat_tail()` calls `run()` with the appropriate
    parameters."""
    # Mock out the run command on an adb instance
    adb = ADB(mock_tools, "exampleDevice")

    # Invoke logcat_tail with a specific timestamp
    adb.logcat_tail(since=datetime(2022, 11, 10, 9, 8, 7))

    # Validate call parameters.
    mock_tools.subprocess.run.assert_called_once_with(
        [
            os.fsdecode(mock_tools.android_sdk.adb_path),
            "-s",
            "exampleDevice",
            "logcat",
            "-t",
            "11-10 09:08:07.000000",
            "-s",
            "MainActivity:*",
            "stdio:*",
            "python.stdout:*",
            "AndroidRuntime:*",
        ],
        env=mock_tools.android_sdk.env,
        check=True,
    )


def test_adb_failure(mock_tools):
    """If adb logcat fails, the error is caught."""
    # Mock out the run command on an adb instance
    adb = ADB(mock_tools, "exampleDevice")
    mock_tools.subprocess.run = MagicMock(
        side_effect=subprocess.CalledProcessError(returncode=1, cmd="adb logcat")
    )

    with pytest.raises(BriefcaseCommandError):
        adb.logcat_tail(since=datetime(2022, 11, 10, 9, 8, 7))
