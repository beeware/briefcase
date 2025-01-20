# Xcode uses the same run implementation as the base app;
# Run a basic test to ensure coverage, but fall back to
# the app backend for exhaustive tests.
import subprocess
from signal import SIGTERM
from unittest import mock

import pytest

from briefcase.console import Console
from briefcase.integrations.subprocess import Subprocess
from briefcase.platforms.macOS import macOS_log_clean_filter
from briefcase.platforms.macOS.xcode import macOSXcodeRunCommand


@pytest.fixture
def run_command(tmp_path):
    command = macOSXcodeRunCommand(
        console=Console(),
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )
    command.tools.home_path = tmp_path / "home"
    command.tools.subprocess = mock.MagicMock(spec_set=Subprocess)
    command._stream_app_logs = mock.MagicMock()

    # To satisfy coverage, the stop function must be invoked
    # at least once when streaming app logs.
    def mock_stream_app_logs(app, stop_func, **kwargs):
        stop_func()

    command._stream_app_logs.side_effect = mock_stream_app_logs
    command.tools.os.kill = mock.MagicMock()

    return command


def test_run_app(run_command, first_app_config, sleep_zero, tmp_path, monkeypatch):
    """A macOS Xcode app can be started."""
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


def test_run_app_with_passthrough(
    run_command,
    first_app_config,
    sleep_zero,
    tmp_path,
    monkeypatch,
):
    """A macOS Xcode app can be started with args."""
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


def test_run_app_test_mode(
    run_command,
    first_app_config,
    sleep_zero,
    tmp_path,
    monkeypatch,
):
    """A macOS Xcode app can be started in test mode."""
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


def test_run_app_test_mode_with_passthrough(
    run_command,
    first_app_config,
    sleep_zero,
    tmp_path,
    monkeypatch,
):
    """A macOS Xcode app can be started in test mode with args."""
    # Mock a popen object that represents the log stream
    log_stream_process = mock.MagicMock(spec_set=subprocess.Popen)
    run_command.tools.subprocess.Popen.return_value = log_stream_process

    # Monkeypatch the tools get the process ID
    monkeypatch.setattr(
        "briefcase.platforms.macOS.get_process_id_by_command", lambda *a, **kw: 100
    )

    # Run app in test mode with args
    run_command.run_app(
        first_app_config,
        test_mode=True,
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
