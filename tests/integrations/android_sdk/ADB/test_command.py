import os
import subprocess
import sys
from pathlib import Path

import pytest

from briefcase.exceptions import InvalidDeviceError
from briefcase.integrations.android_sdk import ADB


def test_simple_command(mock_tools, tmp_path):
    """ADB.command() invokes adb with the provided arguments."""
    # Create an ADB instance and invoke command()
    adb = ADB(mock_tools, "exampleDevice")

    adb.run("example", "command")

    # Check that adb was invoked with the expected commands
    mock_tools.subprocess.check_output.assert_called_once_with(
        [
            os.fsdecode(
                tmp_path
                / "sdk"
                / "platform-tools"
                / f"adb{'.exe' if sys.platform == 'win32' else ''}"
            ),
            "-s",
            "exampleDevice",
            "example",
            "command",
        ],
        stderr=subprocess.STDOUT,
    )


@pytest.mark.parametrize(
    "name, exception",
    [
        # When the device is not found, look for a command the user can run to get a
        # list of valid devices.
        ("device-not-found", InvalidDeviceError),
        # Validate that when an arbitrary adb errors, we print the full adb output.
        # This adb output comes from asking it to run a nonexistent adb command.
        ("arbitrary-adb-error-unknown-command", subprocess.CalledProcessError),
    ],
)
def test_error_handling(mock_tools, tmp_path, name, exception):
    """ADB.command() can parse errors returned by adb."""
    # Set up a mock command with a subprocess module that has with sample data loaded.
    adb_samples = Path(__file__).parent / "adb_errors"
    with (adb_samples / (name + ".out")).open("r") as adb_output_file:
        with (adb_samples / (name + ".returncode")).open(
            encoding="utf-8"
        ) as returncode_file:
            mock_tools.subprocess.check_output.side_effect = (
                subprocess.CalledProcessError(
                    returncode=int(returncode_file.read().strip()),
                    cmd=["ignored"],
                    output=adb_output_file.read(),
                )
            )

    # Create an ADB instance and invoke run()
    adb = ADB(mock_tools, "exampleDevice")
    with pytest.raises(exception):
        adb.run("example", "command")

    # Check that adb was invoked as expected
    mock_tools.subprocess.check_output.assert_called_once_with(
        [
            os.fsdecode(
                tmp_path
                / "sdk"
                / "platform-tools"
                / f"adb{'.exe' if sys.platform == 'win32' else ''}"
            ),
            "-s",
            "exampleDevice",
            "example",
            "command",
        ],
        stderr=subprocess.STDOUT,
    )
