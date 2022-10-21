# Xcode uses the same run implementation as the base app;
# Run a basic test to ensure coverage, but fall back to
# the app backend for exhaustive tests.
import os
import subprocess
from signal import SIGTERM
from unittest.mock import MagicMock

from briefcase.console import Console, Log
from briefcase.integrations.subprocess import Subprocess
from briefcase.platforms.macOS.xcode import macOSXcodeRunCommand


def test_run_app(first_app_config, tmp_path, monkeypatch):
    """A macOS Xcode app can be started."""
    command = macOSXcodeRunCommand(
        logger=Log(),
        console=Console(),
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )
    command.tools.home_path = tmp_path / "home"
    command.tools.subprocess = MagicMock(spec_set=Subprocess)
    log_stream_process = MagicMock(spec_set=subprocess.Popen)
    command.tools.subprocess.Popen.return_value = log_stream_process
    command.tools.os.kill = MagicMock()

    monkeypatch.setattr(
        "briefcase.platforms.macOS.get_process_id_by_command", lambda *a, **kw: 100
    )

    command.run_app(first_app_config)

    # Calls were made to start the app and to start a log stream.
    bin_path = command.binary_path(first_app_config)
    sender = bin_path / "Contents" / "MacOS" / "First App"
    command.tools.subprocess.Popen.assert_called_with(
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
    command.tools.subprocess.run.assert_called_with(
        ["open", "-n", os.fsdecode(bin_path)],
        cwd=tmp_path / "home",
        check=True,
    )
    command.tools.os.kill.assert_called_with(100, SIGTERM)
    command.tools.subprocess.cleanup.assert_called_with(
        "log stream", log_stream_process
    )
