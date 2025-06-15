import subprocess
from unittest import mock

import pytest

from briefcase.console import Console, LogLevel
from briefcase.integrations.subprocess import Subprocess
from briefcase.platforms.windows.app import WindowsAppRunCommand


@pytest.fixture
def run_command(tmp_path):
    command = WindowsAppRunCommand(
        console=Console(),
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )
    command.tools.home_path = tmp_path / "home"
    command.tools.subprocess = mock.MagicMock(spec_set=Subprocess)

    command._stream_app_logs = mock.MagicMock()

    return command


def test_run_gui_app(run_command, first_app_config, tmp_path):
    """A Windows GUI app can be started."""
    # Set up the log streamer to return a known stream
    log_popen = mock.MagicMock()
    run_command.tools.subprocess.Popen.return_value = log_popen

    # Run the app
    run_command.run_app(first_app_config, passthrough=[])

    # The process was started
    run_command.tools.subprocess.Popen.assert_called_with(
        [tmp_path / "base_path/build/first-app/windows/app/src/First App.exe"],
        cwd=tmp_path / "home",
        encoding="UTF-8",
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=1,
    )

    # The streamer was started
    run_command._stream_app_logs.assert_called_once_with(
        first_app_config,
        popen=log_popen,
        clean_output=False,
    )


def test_run_gui_app_with_passthrough(run_command, first_app_config, tmp_path):
    """A Windows GUI app can be started in debug mode with args."""
    run_command.console.verbosity = LogLevel.DEBUG

    # Set up the log streamer to return a known stream
    log_popen = mock.MagicMock()
    run_command.tools.subprocess.Popen.return_value = log_popen

    # Run the app with args
    run_command.run_app(
        first_app_config,
        passthrough=["foo", "--bar"],
    )

    # The process was started
    run_command.tools.subprocess.Popen.assert_called_with(
        [
            tmp_path / "base_path/build/first-app/windows/app/src/First App.exe",
            "foo",
            "--bar",
        ],
        cwd=tmp_path / "home",
        encoding="UTF-8",
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=1,
        env={"BRIEFCASE_DEBUG": "1"},
    )

    # The streamer was started
    run_command._stream_app_logs.assert_called_once_with(
        first_app_config,
        popen=log_popen,
        clean_output=False,
    )


def test_run_gui_app_failed(run_command, first_app_config, tmp_path):
    """If there's a problem starting the GUI app, an exception is raised."""

    run_command.tools.subprocess.Popen.side_effect = OSError

    with pytest.raises(OSError):
        run_command.run_app(first_app_config, passthrough=[])

    # Popen was still invoked, though
    run_command.tools.subprocess.Popen.assert_called_with(
        [tmp_path / "base_path/build/first-app/windows/app/src/First App.exe"],
        cwd=tmp_path / "home",
        encoding="UTF-8",
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=1,
    )

    # No attempt to stream was made
    run_command._stream_app_logs.assert_not_called()


def test_run_console_app(run_command, first_app_config, tmp_path):
    """A Windows GUI app can be started."""
    first_app_config.console_app = True

    # Set up the log streamer to return a known stream
    log_popen = mock.MagicMock()
    run_command.tools.subprocess.Popen.return_value = log_popen

    # Run the app
    run_command.run_app(first_app_config, passthrough=[])

    # The process was started
    run_command.tools.subprocess.run.assert_called_with(
        [tmp_path / "base_path/build/first-app/windows/app/src/first-app.exe"],
        cwd=tmp_path / "home",
        encoding="UTF-8",
        bufsize=1,
        stream_output=False,
    )

    # There is no streamer
    run_command._stream_app_logs.assert_not_called()


def test_run_console_app_with_passthrough(run_command, first_app_config, tmp_path):
    """A Windows console app can be started in debug mode with args."""
    run_command.console.verbosity = LogLevel.DEBUG

    first_app_config.console_app = True

    # Run the app with args
    run_command.run_app(
        first_app_config,
        passthrough=["foo", "--bar"],
    )

    # The process was started
    run_command.tools.subprocess.run.assert_called_with(
        [
            tmp_path / "base_path/build/first-app/windows/app/src/first-app.exe",
            "foo",
            "--bar",
        ],
        cwd=tmp_path / "home",
        encoding="UTF-8",
        bufsize=1,
        stream_output=False,
        env={"BRIEFCASE_DEBUG": "1"},
    )

    # There is no streamer
    run_command._stream_app_logs.assert_not_called()


def test_run_console_app_failed(run_command, first_app_config, tmp_path):
    """If there's a problem starting the console app, an exception is raised."""
    first_app_config.console_app = True

    run_command.tools.subprocess.run.side_effect = OSError

    with pytest.raises(OSError):
        run_command.run_app(first_app_config, passthrough=[])

    # Popen was still invoked, though
    run_command.tools.subprocess.run.assert_called_with(
        [tmp_path / "base_path/build/first-app/windows/app/src/first-app.exe"],
        cwd=tmp_path / "home",
        encoding="UTF-8",
        bufsize=1,
        stream_output=False,
    )

    # No attempt to stream was made
    run_command._stream_app_logs.assert_not_called()


@pytest.mark.parametrize("is_console_app", [True, False])
def test_run_app_test_mode(run_command, first_app_config, is_console_app, tmp_path):
    """A Windows app can be started in test mode."""
    # Test mode apps are always streamed
    first_app_config.console_app = is_console_app
    first_app_config.test_mode = True

    # Set up the log streamer to return a known stream
    log_popen = mock.MagicMock()
    run_command.tools.subprocess.Popen.return_value = log_popen

    # Run the app
    run_command.run_app(first_app_config, passthrough=[])

    # The process was started
    exe_name = "first-app" if is_console_app else "First App"
    run_command.tools.subprocess.Popen.assert_called_with(
        [tmp_path / f"base_path/build/first-app/windows/app/src/{exe_name}.exe"],
        cwd=tmp_path / "home",
        encoding="UTF-8",
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=1,
        env={"BRIEFCASE_MAIN_MODULE": "tests.first_app"},
    )

    # The streamer was started
    run_command._stream_app_logs.assert_called_once_with(
        first_app_config,
        popen=log_popen,
        clean_output=False,
    )


@pytest.mark.parametrize("is_console_app", [True, False])
def test_run_app_test_mode_with_passthrough(
    run_command,
    first_app_config,
    is_console_app,
    tmp_path,
):
    """A Windows app can be started in test mode with args."""
    # Test mode apps are always streamed
    first_app_config.console_app = is_console_app
    first_app_config.test_mode = True

    # Set up the log streamer to return a known stream
    log_popen = mock.MagicMock()
    run_command.tools.subprocess.Popen.return_value = log_popen

    # Run the app with args
    run_command.run_app(
        first_app_config,
        passthrough=["foo", "--bar"],
    )

    # The process was started
    exe_name = "first-app" if is_console_app else "First App"
    run_command.tools.subprocess.Popen.assert_called_with(
        [
            tmp_path / f"base_path/build/first-app/windows/app/src/{exe_name}.exe",
            "foo",
            "--bar",
        ],
        cwd=tmp_path / "home",
        encoding="UTF-8",
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=1,
        env={"BRIEFCASE_MAIN_MODULE": "tests.first_app"},
    )

    # The streamer was started
    run_command._stream_app_logs.assert_called_once_with(
        first_app_config,
        popen=log_popen,
        clean_output=False,
    )
