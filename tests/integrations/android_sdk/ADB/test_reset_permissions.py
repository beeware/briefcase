import subprocess
from unittest.mock import MagicMock

import pytest

from briefcase.exceptions import BriefcaseCommandError


def test_reset_permissions(adb, capsys):
    """Invoking `reset_permissions()` calls `run()` with the appropriate parameters."""
    # Mock out the run command on an adb instance
    adb.run = MagicMock(return_value="example normal adb output")

    # Invoke reset_permissions
    adb.reset_permissions("com.example.sample.package")

    # Validate call parameters.
    adb.run.assert_called_once_with(
        "shell", "pm", "reset-permissions", "-p", "com.example.sample.package"
    )

    # Validate that the normal output of the command was not printed (since there
    # was no error).
    assert "normal adb output" not in capsys.readouterr()


def test_reset_permissions_fail(adb, capsys):
    """If `reset_permissions()` fails, an error is raised."""
    # Mock out the run command on an adb instance
    adb.run = MagicMock(
        side_effect=subprocess.CalledProcessError(
            returncode=69, cmd="reset-permissions"
        )
    )

    # Invoke reset_permissions
    with pytest.raises(BriefcaseCommandError):
        adb.reset_permissions("com.example.sample.package")

    # Validate call parameters.
    adb.run.assert_called_once_with(
        "shell", "pm", "reset-permissions", "-p", "com.example.sample.package"
    )
