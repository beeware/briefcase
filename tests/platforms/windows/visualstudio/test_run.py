# The run command inherits most of its behavior from the common base
# implementation. Do a surface-level verification here, but the app
# tests provide the actual test coverage.
import os
import subprocess
from unittest import mock

import pytest

from briefcase.console import Console, Log
from briefcase.integrations.subprocess import Subprocess
from briefcase.platforms.windows.visualstudio import WindowsVisualStudioRunCommand


@pytest.fixture
def run_command(tmp_path):
    command = WindowsVisualStudioRunCommand(
        logger=Log(),
        console=Console(),
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )
    command.tools.home_path = tmp_path / "home"
    command.tools.subprocess = mock.MagicMock(spec_set=Subprocess)

    command._stream_app_logs = mock.MagicMock()

    return command


def test_run_app(run_command, first_app_config, tmp_path):
    """A windows Visual Studio project app can be started."""

    # Set up the log streamer to return a known stream with a good returncode
    log_popen = mock.MagicMock()
    run_command.tools.subprocess.Popen.return_value = log_popen

    # Run the app
    run_command.run_app(first_app_config, test_mode=False)

    # Popen was called
    run_command.tools.subprocess.Popen.assert_called_with(
        [
            os.fsdecode(
                tmp_path
                / "base_path"
                / "windows"
                / "VisualStudio"
                / "First App"
                / "x64"
                / "Release"
                / "First App.exe"
            ),
        ],
        cwd=tmp_path / "home",
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=1,
    )

    # The streamer was started
    run_command._stream_app_logs.assert_called_once_with(
        first_app_config,
        popen=log_popen,
        test_mode=False,
        clean_output=False,
    )
