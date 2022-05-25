# Xcode uses the same run implementation as the base app;
# Run a basic test to ensure coverage, but fall back to
# the app backend for exhaustive tests.
import os
import subprocess
from unittest import mock

from briefcase.platforms.macOS.xcode import macOSXcodeRunCommand


def test_run_app(first_app_config, tmp_path):
    """A macOS Xcode app can be started."""
    command = macOSXcodeRunCommand(base_path=tmp_path)
    command.subprocess = mock.MagicMock()

    command.run_app(first_app_config)

    # Calls were made to start the app and to start a log stream.
    bin_path = command.binary_path(first_app_config)
    sender = bin_path / "Contents" / "MacOS" / "First App"
    command.subprocess.Popen.assert_called_with(
        [
            "log",
            "stream",
            "--style",
            "compact",
            "--predicate",
            f'senderImagePath=="{sender}"'
            f' OR (processImagePath=="{sender}"'
            ' AND senderImagePath=="/usr/lib/libffi.dylib")',
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=1,
    )
    command.subprocess.run.assert_called_with(
        ["open", "-n", os.fsdecode(bin_path)], check=True
    )
