from pathlib import Path
from subprocess import CalledProcessError
from unittest.mock import MagicMock

import pytest

from briefcase.exceptions import BriefcaseCommandError
from briefcase.integrations.adb import ADB


def test_simple_command(tmp_path):
    """ADB.command() invokes adb with the provided arguments."""
    cmd = MagicMock()
    cmd.subprocess = MagicMock()
    cmd.android_sdk_home_path = tmp_path

    # Create an ADB instance and invoke command()
    adb = ADB(cmd, "exampleDevice")
    adb.command("example", "command")

    # Check that adb was invoked with the expected commands
    cmd.subprocess.check_output.assert_called_once_with(
        [
            str(tmp_path / "platform-tools" / "adb"),
            "-s",
            "exampleDevice",
            "example",
            "command",
        ],
        stderr=cmd.subprocess.STDOUT,
    )


@pytest.mark.parametrize(
    "name, exception_text",
    [
        # When the device is not found, look for a command the user can run to get a
        # list of valid devices.
        ("device-not-found", "adb devices -l"),
        # Validate that when an arbitrary adb errors, we print the full adb output.
        # This adb output comes from asking it to run a nonexistent adb command.
        ("arbitrary-adb-error-unknown-command", "unknown command"),
    ],
)
def test_error_handling(tmp_path, name, exception_text):
    "ADB.command() can parse errors returned by adb."
    # Set up a mock command with a subprocess module that has with sample data loaded.
    cmd = MagicMock()
    cmd.subprocess = MagicMock()
    cmd.android_sdk_home_path = tmp_path

    adb_samples = Path(__file__).parent / "adb_errors"
    with (adb_samples / (name + ".txt")).open("rb") as adb_output_file:
        with (adb_samples / (name + ".returncode")).open() as returncode_file:
            cmd.subprocess.check_output.side_effect = CalledProcessError(
                returncode=int(returncode_file.read().strip()),
                cmd=["ignored"],
                output=adb_output_file.read(),
            )

    # Create an ADB instance and invoke run()
    adb = ADB(cmd, "exampleDevice")
    with pytest.raises(BriefcaseCommandError) as exc_info:
        adb.command("example", "command")

    # Check that adb was invoked as expected
    cmd.subprocess.check_output.assert_called_once_with(
        [
            str(tmp_path / "platform-tools" / "adb"),
            "-s",
            "exampleDevice",
            "example",
            "command",
        ],
        stderr=cmd.subprocess.STDOUT,
    )

    # Look for the expected exception text.
    assert exception_text in str(exc_info.value)
