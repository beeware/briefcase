import subprocess
from signal import SIGTERM
from unittest import mock

import pytest

from briefcase.console import Console, LogLevel
from briefcase.exceptions import BriefcaseCommandError
from briefcase.integrations.subprocess import Subprocess
from briefcase.platforms.macOS import macOS_log_clean_filter
from briefcase.platforms.macOS.app import macOSAppRunCommand


@pytest.fixture
def run_command(tmp_path):
    command = macOSAppRunCommand(
        console=Console(),
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )
    command.tools.home_path = tmp_path / "home"
    command.tools.subprocess = mock.MagicMock(spec_set=Subprocess)
    command._stream_app_logs = mock.MagicMock()

    # To satisfy coverage, the stop function must be invoked
    # at least once when streaming app logs.
    def mock_stream_app_logs(app, stop_func=lambda: 1 + 1, **kwargs):
        stop_func()

    command._stream_app_logs.side_effect = mock_stream_app_logs
    command.tools.os.kill = mock.MagicMock()

    return command


def test_run_gui_app(run_command, first_app_config, sleep_zero, tmp_path, monkeypatch):
    """A macOS GUI app can be started."""
    # Mock a popen object that represents the log stream
    log_stream_process = mock.MagicMock(spec_set=subprocess.Popen)
    run_command.tools.subprocess.Popen.return_value = log_stream_process

    # Monkeypatch the tools get the process ID
    monkeypatch.setattr(
        "briefcase.platforms.macOS.get_process_id_by_command", lambda *a, **kw: 100
    )

    run_command.run_app(first_app_config, test_mode=False, passthrough=[])

    # Calls were made to start the app and to start a log stream.
    bin_path = run_command.binary_path(first_app_config)
    sender = bin_path / "Contents/MacOS/First App"
    run_command.tools.subprocess.Popen.assert_called_with(
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
    run_command.tools.subprocess.run.assert_called_with(
        ["open", "-n", bin_path],
        cwd=tmp_path / "home",
        check=True,
    )

    # The log stream was started
    run_command._stream_app_logs.assert_called_with(
        first_app_config,
        popen=log_stream_process,
        test_mode=False,
        clean_filter=macOS_log_clean_filter,
        clean_output=True,
        stop_func=mock.ANY,
        log_stream=True,
    )

    # The app process was killed on exit.
    run_command.tools.os.kill.assert_called_with(100, SIGTERM)


def test_run_gui_app_with_passthrough(
    run_command,
    first_app_config,
    sleep_zero,
    tmp_path,
    monkeypatch,
):
    """A macOS app can be started in debug mode with args."""
    run_command.console.verbosity = LogLevel.DEBUG

    # Mock a popen object that represents the log stream
    log_stream_process = mock.MagicMock(spec_set=subprocess.Popen)
    run_command.tools.subprocess.Popen.return_value = log_stream_process

    # Monkeypatch the tools get the process ID
    monkeypatch.setattr(
        "briefcase.platforms.macOS.get_process_id_by_command", lambda *a, **kw: 100
    )

    # Run the app with args
    run_command.run_app(
        first_app_config,
        test_mode=False,
        passthrough=["foo", "--bar"],
    )

    # Calls were made to start the app and to start a log stream.
    bin_path = run_command.binary_path(first_app_config)
    sender = bin_path / "Contents/MacOS/First App"
    run_command.tools.subprocess.Popen.assert_called_with(
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
    run_command.tools.subprocess.run.assert_called_with(
        ["open", "-n", bin_path, "--args", "foo", "--bar"],
        cwd=tmp_path / "home",
        check=True,
        env={"BRIEFCASE_DEBUG": "1"},
    )

    # The log stream was started
    run_command._stream_app_logs.assert_called_with(
        first_app_config,
        popen=log_stream_process,
        test_mode=False,
        clean_filter=macOS_log_clean_filter,
        clean_output=True,
        stop_func=mock.ANY,
        log_stream=True,
    )

    # The app process was killed on exit.
    run_command.tools.os.kill.assert_called_with(100, SIGTERM)


def test_run_gui_app_failed(run_command, first_app_config, sleep_zero, tmp_path):
    """If there's a problem started the app, an exception is raised."""
    # Mock a failure opening the app
    run_command.tools.subprocess.run.side_effect = subprocess.CalledProcessError(
        cmd=["open", "-n", run_command.binary_path(first_app_config)],
        returncode=1,
    )

    with pytest.raises(BriefcaseCommandError):
        run_command.run_app(first_app_config, test_mode=False, passthrough=[])

    # Calls were made to start the app and to start a log stream.
    bin_path = run_command.binary_path(first_app_config)
    sender = bin_path / "Contents/MacOS/First App"
    run_command.tools.subprocess.Popen.assert_called_with(
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
    run_command.tools.subprocess.run.assert_called_with(
        ["open", "-n", bin_path],
        cwd=tmp_path / "home",
        check=True,
    )

    # No attempt was made to stream the log or cleanup
    run_command._stream_app_logs.assert_not_called()
    run_command.tools.os.kill.assert_not_called()


def test_run_gui_app_find_pid_failed(
    run_command,
    first_app_config,
    sleep_zero,
    tmp_path,
    monkeypatch,
    capsys,
):
    """If after app is started, its pid is not found, do not stream output."""
    # Mock a failed PID lookup
    monkeypatch.setattr(
        "briefcase.platforms.macOS.get_process_id_by_command",
        lambda *a, **kw: None,
    )

    with pytest.raises(BriefcaseCommandError) as exc_info:
        run_command.run_app(first_app_config, test_mode=False, passthrough=[])

    # Calls were made to start the app and to start a log stream.
    bin_path = run_command.binary_path(first_app_config)
    sender = bin_path / "Contents/MacOS/First App"
    run_command.tools.subprocess.Popen.assert_called_with(
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
    run_command.tools.subprocess.run.assert_called_with(
        ["open", "-n", bin_path],
        cwd=tmp_path / "home",
        check=True,
    )
    assert exc_info.value.msg == (
        "Unable to find process for app first-app to start log streaming."
    )

    # No attempt was made to stream the log or cleanup
    run_command._stream_app_logs.assert_not_called()
    run_command.tools.os.kill.assert_not_called()


def test_run_gui_app_test_mode(
    run_command,
    first_app_config,
    sleep_zero,
    tmp_path,
    monkeypatch,
):
    """A macOS GUI app can be started in test mode."""
    # Mock a popen object that represents the log stream
    log_stream_process = mock.MagicMock(spec_set=subprocess.Popen)
    run_command.tools.subprocess.Popen.return_value = log_stream_process

    # Monkeypatch the tools get the process ID
    monkeypatch.setattr(
        "briefcase.platforms.macOS.get_process_id_by_command", lambda *a, **kw: 100
    )

    run_command.run_app(first_app_config, test_mode=True, passthrough=[])

    # Calls were made to start the app and to start a log stream.
    bin_path = run_command.binary_path(first_app_config)
    sender = bin_path / "Contents/MacOS/First App"
    run_command.tools.subprocess.Popen.assert_called_with(
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
    run_command.tools.subprocess.run.assert_called_with(
        ["open", "-n", bin_path],
        cwd=tmp_path / "home",
        check=True,
        env={"BRIEFCASE_MAIN_MODULE": "tests.first_app"},
    )

    # The log stream was started
    run_command._stream_app_logs.assert_called_with(
        first_app_config,
        popen=log_stream_process,
        test_mode=True,
        clean_filter=macOS_log_clean_filter,
        clean_output=True,
        stop_func=mock.ANY,
        log_stream=True,
    )

    # The app process was killed on exit.
    run_command.tools.os.kill.assert_called_with(100, SIGTERM)


def test_run_console_app(run_command, first_app_config, tmp_path):
    """A macOS console app can be started."""
    # Set the app to be a console app
    first_app_config.console_app = True

    run_command.run_app(first_app_config, test_mode=False, passthrough=[])

    # Calls were made to start the app and to start a log stream.
    bin_path = run_command.binary_path(first_app_config)
    run_command.tools.subprocess.run.assert_called_with(
        [bin_path / "Contents/MacOS/First App"],
        cwd=tmp_path / "home",
        check=True,
        stream_output=False,
    )

    # The log stream was not started
    run_command._stream_app_logs.assert_not_called()


def test_run_console_app_with_passthrough(
    run_command,
    first_app_config,
    tmp_path,
):
    """A macOS console app can be started in debug mode with args."""
    run_command.console.verbosity = LogLevel.DEBUG

    # Set the app to be a console app
    first_app_config.console_app = True

    # Run the app with args
    run_command.run_app(
        first_app_config,
        test_mode=False,
        passthrough=["foo", "--bar"],
    )

    # Calls were made to start the app and to start a log stream.
    bin_path = run_command.binary_path(first_app_config)
    run_command.tools.subprocess.run.assert_called_with(
        [bin_path / "Contents/MacOS/First App", "foo", "--bar"],
        cwd=tmp_path / "home",
        check=True,
        stream_output=False,
        env={"BRIEFCASE_DEBUG": "1"},
    )

    # The log stream was not started
    run_command._stream_app_logs.assert_not_called()


def test_run_console_app_test_mode(run_command, first_app_config, sleep_zero, tmp_path):
    """A macOS console app can be started in test mode."""
    first_app_config.console_app = True

    # Mock a popen object that represents the app
    app_process = mock.MagicMock(spec_set=subprocess.Popen)
    run_command.tools.subprocess.Popen.return_value = app_process

    run_command.run_app(first_app_config, test_mode=True, passthrough=[])

    # Calls were made to start the app and to start a log stream.
    bin_path = run_command.binary_path(first_app_config)
    run_command.tools.subprocess.Popen.assert_called_with(
        [bin_path / "Contents/MacOS/First App"],
        cwd=tmp_path / "home",
        env={"BRIEFCASE_MAIN_MODULE": "tests.first_app"},
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=1,
    )

    # The log stream was not started
    run_command._stream_app_logs.assert_called_with(
        first_app_config,
        popen=app_process,
        test_mode=True,
    )


def test_run_console_app_test_mode_with_passthrough(
    run_command,
    first_app_config,
    sleep_zero,
    tmp_path,
):
    """A macOS console app can be started in test mode with parameters and debug
    mode."""
    run_command.console.verbosity = LogLevel.DEBUG

    first_app_config.console_app = True

    # Mock a popen object that represents the app
    app_process = mock.MagicMock(spec_set=subprocess.Popen)
    run_command.tools.subprocess.Popen.return_value = app_process

    run_command.run_app(first_app_config, test_mode=True, passthrough=["foo", "--bar"])

    # Calls were made to start the app and to start a log stream.
    bin_path = run_command.binary_path(first_app_config)
    run_command.tools.subprocess.Popen.assert_called_with(
        [bin_path / "Contents/MacOS/First App", "foo", "--bar"],
        cwd=tmp_path / "home",
        env={"BRIEFCASE_DEBUG": "1", "BRIEFCASE_MAIN_MODULE": "tests.first_app"},
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=1,
    )

    # The log stream was not started
    run_command._stream_app_logs.assert_called_with(
        first_app_config,
        popen=app_process,
        test_mode=True,
    )


def test_run_console_app_failed(run_command, first_app_config, sleep_zero, tmp_path):
    """If there's a problem started a console app, an exception is raised."""
    # Set the app to be a console app
    first_app_config.console_app = True

    # Mock a failure opening the app
    run_command.tools.subprocess.run.side_effect = subprocess.CalledProcessError(
        cmd=[run_command.binary_path(first_app_config) / "Contents/MacOS/First App"],
        returncode=1,
    )

    # Although the command raises an error, this could be because the script itself
    # raised an error.
    run_command.run_app(first_app_config, test_mode=False, passthrough=[])

    # Calls were made to start the app and to start a log stream.
    bin_path = run_command.binary_path(first_app_config)
    run_command.tools.subprocess.run.assert_called_with(
        [bin_path / "Contents/MacOS/First App"],
        cwd=tmp_path / "home",
        stream_output=False,
        check=True,
    )

    # No attempt was made to stream the log or cleanup
    run_command._stream_app_logs.assert_not_called()
