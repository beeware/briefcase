import os
import subprocess
from unittest.mock import MagicMock

import pytest

from briefcase.exceptions import BriefcaseCommandError


def test_kill(mock_tools, adb):
    """An emulator can be killed."""
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


def test_kill_failure(adb):
    """If emu kill fails, the error is caught."""
    # Mock out the run command on an adb instance
    adb.run = MagicMock(
        side_effect=subprocess.CalledProcessError(returncode=1, cmd="adb emu kill")
    )

    with pytest.raises(BriefcaseCommandError):
        adb.kill()
