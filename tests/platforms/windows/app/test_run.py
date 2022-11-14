import os
import subprocess
from unittest import mock

import pytest

from briefcase.console import Console, Log
from briefcase.exceptions import BriefcaseCommandError
from briefcase.integrations.subprocess import Subprocess
from briefcase.platforms.windows.app import WindowsAppRunCommand


@pytest.fixture
def run_command(first_app_config, tmp_path):
    command = WindowsAppRunCommand(
        logger=Log(),
        console=Console(),
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )
    command.tools.home_path = tmp_path / "home"
    command.tools.subprocess = mock.MagicMock(spec_set=Subprocess)

    return command


def test_run_app(run_command, first_app_config, tmp_path):
    """A Windows app can be started."""
    # Set up the log streamer to return a known stream with a good returncode
    log_popen = mock.MagicMock()
    log_popen.returncode = 0
    run_command.tools.subprocess.Popen.return_value = log_popen

    # Run the app
    run_command.run_app(first_app_config)

    # The process was started
    run_command.tools.subprocess.Popen.assert_called_with(
        [
            os.fsdecode(
                tmp_path
                / "base_path"
                / "windows"
                / "app"
                / "First App"
                / "src"
                / "First App.exe"
            ),
        ],
        cwd=tmp_path / "home",
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=1,
    )

    # The streamer was started
    run_command.tools.subprocess.stream_output.assert_called_once_with(
        "first-app",
        log_popen,
    )

    # The stream was cleaned up
    run_command.tools.subprocess.cleanup.assert_called_once_with("first-app", log_popen)


def test_run_app_failed(run_command, first_app_config, tmp_path):
    """If there's a problem started the app, an exception is raised."""

    run_command.tools.subprocess.Popen.side_effect = OSError

    with pytest.raises(BriefcaseCommandError, match=r"Unable to start app first-app."):
        run_command.run_app(first_app_config)

    # Popen was still invoked, though
    run_command.tools.subprocess.Popen.assert_called_with(
        [
            os.fsdecode(
                tmp_path
                / "base_path"
                / "windows"
                / "app"
                / "First App"
                / "src"
                / "First App.exe"
            ),
        ],
        cwd=tmp_path / "home",
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=1,
    )

    # No attempt to stream was made
    run_command.tools.subprocess.stream_output.assert_not_called()


def test_run_app_error(run_command, first_app_config, tmp_path):
    """If a Windows app raises an error, the error is caught."""
    # Set up the log streamer to return a known stream with a bad returncode
    log_popen = mock.MagicMock()
    log_popen.returncode = 42
    run_command.tools.subprocess.Popen.return_value = log_popen

    # Run the app
    with pytest.raises(
        BriefcaseCommandError,
        match=r"Problem running app first-app",
    ):
        run_command.run_app(first_app_config)

    # The process was started
    run_command.tools.subprocess.Popen.assert_called_with(
        [
            os.fsdecode(
                tmp_path
                / "base_path"
                / "windows"
                / "app"
                / "First App"
                / "src"
                / "First App.exe"
            ),
        ],
        cwd=tmp_path / "home",
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=1,
    )

    # The streamer was started
    run_command.tools.subprocess.stream_output.assert_called_once_with(
        "first-app",
        log_popen,
    )

    # The stream was cleaned up
    run_command.tools.subprocess.cleanup.assert_called_once_with("first-app", log_popen)


def test_run_app_ctrl_c(run_command, first_app_config, tmp_path, capsys):
    """When CTRL-C is sent while the App is running, Briefcase exits
    normally."""
    # Set up the log streamer to return a known stream
    log_popen = mock.MagicMock()
    run_command.tools.subprocess.Popen.return_value = log_popen

    # Mock the effect of CTRL-C being hit while streaming
    run_command.tools.subprocess.stream_output.side_effect = KeyboardInterrupt

    # Invoke run_app (and KeyboardInterrupt does not surface)
    run_command.run_app(first_app_config)

    # App is started
    run_command.tools.subprocess.Popen.assert_called_with(
        [
            os.fsdecode(
                tmp_path
                / "base_path"
                / "windows"
                / "app"
                / "First App"
                / "src"
                / "First App.exe"
            ),
        ],
        cwd=tmp_path / "home",
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=1,
    )

    # An attempt was made to stream
    run_command.tools.subprocess.stream_output.assert_called_once_with(
        "first-app",
        log_popen,
    )

    # Shows the try block for KeyboardInterrupt was entered
    assert capsys.readouterr().out.endswith(
        "[first-app] Starting app...\n"
        "===========================================================================\n"
    )

    # The stream was cleaned up
    run_command.tools.subprocess.cleanup.assert_called_once_with("first-app", log_popen)
