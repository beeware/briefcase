import os
import subprocess
from unittest import mock

from briefcase.integrations.android_sdk import ADB


def test_logcat(mock_tools):
    """Invoking `logcat()` calls `Popen()` with the appropriate parameters."""
    # Mock out the run command on an adb instance
    adb = ADB(mock_tools, "exampleDevice")

    # Mock the result of calling Popen so we can compare against this return value
    popen = mock.MagicMock()
    mock_tools.subprocess.Popen.return_value = popen

    # Invoke logcat
    result = adb.logcat("1234")

    # Validate call parameters.
    mock_tools.subprocess.Popen.assert_called_once_with(
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
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=1,
    )

    # The Popen object is returned
    assert result == popen
