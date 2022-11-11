import subprocess
from unittest import mock

import pytest

from briefcase.console import Console, Log
from briefcase.exceptions import BriefcaseCommandError
from briefcase.integrations.flatpak import Flatpak
from briefcase.integrations.subprocess import Subprocess
from briefcase.platforms.linux.flatpak import LinuxFlatpakRunCommand


@pytest.fixture
def run_command(tmp_path):
    command = LinuxFlatpakRunCommand(
        logger=Log(),
        console=Console(),
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )
    command.tools.flatpak = mock.MagicMock(spec_set=Flatpak)
    command.tools.subprocess = mock.MagicMock(spec_set=Subprocess)

    return command


def test_run(run_command, first_app_config):
    """A flatpak can be executed."""
    # Set up the log streamer to return a known stream
    log_popen = mock.MagicMock()
    run_command.tools.flatpak.run.return_value = log_popen

    # Set a normal return code for the process
    log_popen.poll.return_value = 0

    # To satisfy coverage, the stop function must be invoked at least once
    # when invoking stream_output.
    def mock_stream_output(label, popen_process, stop_func):
        stop_func()

    run_command.tools.subprocess.stream_output.side_effect = mock_stream_output

    # Run the app
    run_command.run_app(first_app_config)

    # App is executed
    run_command.tools.flatpak.run.assert_called_once_with(
        bundle="com.example",
        app_name="first-app",
    )

    # The streamer was started
    run_command.tools.subprocess.stream_output.assert_called_once_with(
        "log stream", log_popen, stop_func=mock.ANY
    )

    # The app was polled twice; once by the stream stop function,
    # and once in the finally block.
    assert log_popen.poll.mock_calls == [mock.call()] * 2


def test_run_app_failed(run_command, first_app_config, tmp_path):
    """If there's a problem starting the app, an exception is raised."""
    run_command.tools.flatpak.run.side_effect = OSError

    with pytest.raises(BriefcaseCommandError):
        run_command.run_app(first_app_config)

    # The run command was still invoked
    run_command.tools.flatpak.run.assert_called_once_with(
        bundle="com.example",
        app_name="first-app",
    )

    # No attempt to stream was made
    run_command.tools.subprocess.stream_output.assert_not_called()


def test_run_ctrl_c(run_command, first_app_config, capsys):
    """When CTRL-C is sent while the App is running, Briefcase exits
    normally."""
    # Set up the log streamer to return a known stream
    log_popen = mock.MagicMock()
    run_command.tools.flatpak.run.return_value = log_popen

    # When polled, the process is still running
    log_popen.poll.return_value = None

    # Mock the effect of CTRL-C being hit while streaming
    run_command.tools.subprocess.stream_output.side_effect = KeyboardInterrupt

    # Invoke run_app (and KeyboardInterrupt does not surface)
    run_command.run_app(first_app_config)

    # App is executed
    run_command.tools.flatpak.run.assert_called_once_with(
        bundle="com.example",
        app_name="first-app",
    )

    # An attempt was made to stream
    run_command.tools.subprocess.stream_output.assert_called_once_with(
        "log stream", log_popen, stop_func=mock.ANY
    )

    # Shows the try block for KeyboardInterrupt was entered
    assert capsys.readouterr().out.endswith(
        "[first-app] Starting app...\n"
        "\n"
        "[first-app] Following log output (type CTRL-C to stop log)...\n"
        "===========================================================================\n"
    )

    # The app was poll in the finally block
    log_popen.poll.assert_called_once_with()

    # A successful attempt to terminate occured
    log_popen.terminate.assert_called_once_with()
    log_popen.wait.assert_called_once_with(timeout=3)

    # No kill call was made
    log_popen.kill.assert_not_called()


def test_run_app_terminate_failure(run_command, first_app_config, capsys):
    """If the app can't be terminated on exit, it's force killed.."""
    # Set up the log streamer to return a known stream
    log_popen = mock.MagicMock()
    run_command.tools.flatpak.run.return_value = log_popen

    # When polled, the process is still running
    log_popen.poll.return_value = None

    # Mock the effect of an unsuccessful termination.
    log_popen.wait.side_effect = subprocess.TimeoutExpired(cmd="appimage", timeout=3)

    # Mock the effect of CTRL-C being hit while streaming
    run_command.tools.subprocess.stream_output.side_effect = KeyboardInterrupt

    # Invoke run_app (and KeyboardInterrupt does not surface)
    run_command.run_app(first_app_config)

    # App is executed
    run_command.tools.flatpak.run.assert_called_once_with(
        bundle="com.example",
        app_name="first-app",
    )

    # An attempt was made to stream
    run_command.tools.subprocess.stream_output.assert_called_once_with(
        "log stream", log_popen, stop_func=mock.ANY
    )

    # Shows the try block for KeyboardInterrupt was entered
    assert capsys.readouterr().out.endswith(
        "[first-app] Starting app...\n"
        "\n"
        "[first-app] Following log output (type CTRL-C to stop log)...\n"
        "===========================================================================\n"
        "Forcibly killing first-app...\n"
    )

    # The app was polled in the finally block
    log_popen.poll.assert_called_once_with()

    # A successful attempt to terminate occured
    log_popen.terminate.assert_called_once_with()
    log_popen.wait.assert_called_once_with(timeout=3)

    # A kill call was made
    log_popen.kill.assert_called_once_with()
