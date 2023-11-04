import os
import subprocess
import sys
from pathlib import Path

import pytest

from briefcase.exceptions import BriefcaseCommandError, InvalidDeviceError


def test_simple_command(mock_tools, adb, tmp_path):
    """ADB.run() invokes adb with the provided arguments."""
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
        quiet=False,
    )


def test_quiet_command(mock_tools, adb, tmp_path):
    """ADB.run() can be invoked in quiet mode."""
    adb.run("example", "command", quiet=True)

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
        quiet=True,
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
def test_error_handling(mock_tools, adb, name, exception, tmp_path):
    """ADB.run() can parse errors returned by adb."""
    # Set up a mock command with a subprocess module that has with sample data loaded.
    adb_samples = Path(__file__).parent / "adb_errors"
    with (adb_samples / (name + ".out")).open("r", encoding="utf-8") as adb_output_file:
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

    # invoke run()
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
        quiet=False,
    )


def test_older_sdk_error(mock_tools, adb):
    """Failure [INSTALL_FAILED_OLDER_SDK] needs to be caught manually."""
    mock_tools.subprocess.check_output.return_value = "\n".join(
        [
            "Performing Push Install",
            "C:/.../app-debug.apk: 1 file pushed, 0 skipped. 5.5 MB/s (33125287 bytes in 5.768s)",
            "         pkg: /data/local/tmp/app-debug.apk",
            "Failure [INSTALL_FAILED_OLDER_SDK]",
        ]
    )
    with pytest.raises(
        BriefcaseCommandError,
        match=r"Your device doesn't meet the minimum SDK requirements of this app",
    ):
        adb.run("example", "command")
