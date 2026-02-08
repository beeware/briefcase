import subprocess
from unittest.mock import MagicMock

import pytest

from briefcase.exceptions import BriefcaseCommandError


def test_revoke_permission(adb, capsys):
    """Invoking `revoke_permission()` calls `run()` with the appropriate parameters."""
    # Mock out the run command on an adb instance
    adb.run = MagicMock(return_value="example normal adb output")

    # Invoke revoke_permission
    adb.revoke_permission(
        "com.example.sample.package", "android.permission.BLUETOOTH_SCAN"
    )

    # Validate call parameters.
    adb.run.assert_called_once_with(
        "shell",
        "pm",
        "revoke",
        "com.example.sample.package",
        "android.permission.BLUETOOTH_SCAN",
    )

    # Validate that the normal output of the command was not printed (since there
    # was no error).
    assert "normal adb output" not in capsys.readouterr()


def test_revoke_permission_fail(adb):
    """If `revoke_permission()` fails, an error is raised."""
    # Mock out the run command on an adb instance
    adb.run = MagicMock(
        side_effect=subprocess.CalledProcessError(
            returncode=69, cmd="revoke-permission"
        )
    )

    # Invoke revoke_permission
    with pytest.raises(BriefcaseCommandError):
        adb.revoke_permission(
            "com.example.sample.package", "android.permission.BLUETOOTH_SCAN"
        )

    # Validate call parameters.
    adb.run.assert_called_once_with(
        "shell",
        "pm",
        "revoke",
        "com.example.sample.package",
        "android.permission.BLUETOOTH_SCAN",
    )
