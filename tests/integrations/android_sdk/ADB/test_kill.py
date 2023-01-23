import os
import subprocess
from unittest.mock import MagicMock

import pytest

from briefcase.exceptions import BriefcaseCommandError
from briefcase.integrations.android_sdk import ADB


def test_kill(mock_tools):
    """An emulator can be killed."""
    # Mock out the run command on an adb instance
    adb = ADB(mock_tools, "exampleDevice")

    # Invoke kill
    adb.kill()

    # Validate call parameters.
    mock_tools.subprocess.check_output.assert_called_once_with(
        [
            os.fsdecode(mock_tools.android_sdk.adb_path),
            "-s",
            "exampleDevice",
            "emu",
            "kill",
        ],
        quiet=False,
    )


def test_kill_failure(mock_tools):
    """If emu kill fails, the error is caught."""
    # Mock out the run command on an adb instance
    adb = ADB(mock_tools, "exampleDevice")
    adb.run = MagicMock(
        side_effect=subprocess.CalledProcessError(returncode=1, cmd="adb emu kill")
    )

    with pytest.raises(BriefcaseCommandError):
        adb.kill()
