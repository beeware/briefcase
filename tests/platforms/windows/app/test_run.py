import json
import platform
import subprocess
from unittest import mock

import pytest

from briefcase.console import LogLevel
from briefcase.exceptions import BriefcaseCommandError
from briefcase.integrations.subprocess import Subprocess
from briefcase.platforms.windows.app import WindowsAppRunCommand

from ....utils import create_file


@pytest.fixture
def run_command(dummy_console, tmp_path):
    command = WindowsAppRunCommand(
        console=dummy_console,
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )
    command.tools.home_path = tmp_path / "home"
    command.tools.subprocess = mock.MagicMock(spec_set=Subprocess)

    command._stream_app_logs = mock.MagicMock()

    return command


@pytest.fixture
def startup_log(tmp_path):
    """The startup diagnostics log location passed to every app."""
    return {
        "BRIEFCASE_STARTUP_LOG": str(tmp_path / "base_path/logs/first-app.startup.log")
    }


def test_run_gui_app(run_command, first_app_config, tmp_path, startup_log):
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
        env=startup_log,
    )

    # The streamer was started
    run_command._stream_app_logs.assert_called_once_with(
        first_app_config,
        popen=log_popen,
        clean_output=False,
    )


def test_run_gui_app_with_passthrough(
    run_command,
    first_app_config,
    tmp_path,
    startup_log,
):
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
        env={"BRIEFCASE_DEBUG": "1", **startup_log},
    )

    # The streamer was started
    run_command._stream_app_logs.assert_called_once_with(
        first_app_config,
        popen=log_popen,
        clean_output=False,
    )


def test_run_gui_app_failed(run_command, first_app_config, tmp_path, startup_log):
    """If there's a problem starting the GUI app, an exception is raised."""

    run_command.tools.subprocess.Popen.side_effect = OSError("Some error")

    with pytest.raises(OSError, match="Some error"):
        run_command.run_app(first_app_config, passthrough=[])

    # Popen was still invoked, though
    run_command.tools.subprocess.Popen.assert_called_with(
        [tmp_path / "base_path/build/first-app/windows/app/src/First App.exe"],
        cwd=tmp_path / "home",
        encoding="UTF-8",
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=1,
        env=startup_log,
    )

    # No attempt to stream was made
    run_command._stream_app_logs.assert_not_called()


def test_run_console_app(run_command, first_app_config, tmp_path, startup_log):
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
        env=startup_log,
    )

    # There is no streamer
    run_command._stream_app_logs.assert_not_called()


def test_run_console_app_with_passthrough(
    run_command,
    first_app_config,
    tmp_path,
    startup_log,
):
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
        env={"BRIEFCASE_DEBUG": "1", **startup_log},
    )

    # There is no streamer
    run_command._stream_app_logs.assert_not_called()


def test_run_console_app_failed(
    run_command,
    first_app_config,
    tmp_path,
    startup_log,
):
    """If there's a problem starting the console app, an exception is raised."""
    first_app_config.console_app = True

    run_command.tools.subprocess.run.side_effect = OSError("Some error")

    with pytest.raises(OSError, match="Some error"):
        run_command.run_app(first_app_config, passthrough=[])

    # Popen was still invoked, though
    run_command.tools.subprocess.run.assert_called_with(
        [tmp_path / "base_path/build/first-app/windows/app/src/first-app.exe"],
        cwd=tmp_path / "home",
        encoding="UTF-8",
        bufsize=1,
        stream_output=False,
        env=startup_log,
    )

    # No attempt to stream was made
    run_command._stream_app_logs.assert_not_called()


@pytest.mark.parametrize("is_console_app", [True, False])
def test_run_app_test_mode(
    run_command,
    first_app_config,
    is_console_app,
    tmp_path,
    startup_log,
):
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
        env={"BRIEFCASE_MAIN_MODULE": "tests.first_app", **startup_log},
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
    startup_log,
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
        env={"BRIEFCASE_MAIN_MODULE": "tests.first_app", **startup_log},
    )

    # The streamer was started
    run_command._stream_app_logs.assert_called_once_with(
        first_app_config,
        popen=log_popen,
        clean_output=False,
    )


def test_run_gui_app_debugger(
    run_command,
    first_app_config,
    tmp_path,
    dummy_debugger,
    startup_log,
):
    """A Windows app can be started in debug mode."""
    # Set up the log streamer to return a known stream
    log_popen = mock.MagicMock()
    run_command.tools.subprocess.Popen.return_value = log_popen

    first_app_config.debugger = dummy_debugger
    first_app_config.debugger_host = "somehost"
    first_app_config.debugger_port = 9999

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
        env={
            "BRIEFCASE_DEBUGGER": json.dumps(
                {
                    "debugger": "dummy",
                    "host": "somehost",
                    "port": 9999,
                    "host_os": platform.system(),
                    "app_path_mappings": {
                        "device_sys_path_regex": "app$",
                        "device_subfolders": ["first_app"],
                        "host_folders": [str(tmp_path / "base_path/src/first_app")],
                    },
                    "app_packages_path_mappings": None,
                }
            ),
            **startup_log,
        },
    )

    # The streamer was started
    run_command._stream_app_logs.assert_called_once_with(
        first_app_config,
        popen=log_popen,
        clean_output=False,
    )


def test_startup_log_is_cleared(run_command, first_app_config, tmp_path):
    """Any startup log from a previous run is removed before the app starts."""
    log_path = tmp_path / "base_path/logs/first-app.startup.log"
    create_file(log_path, "stale content from a previous run")

    run_command.run_app(first_app_config, passthrough=[])

    # The stale log was removed, and not recreated (the app is a mock, so it
    # doesn't write anything).
    assert not log_path.exists()


def test_startup_log_reported_on_failure(
    run_command,
    first_app_config,
    tmp_path,
    capsys,
):
    """If the app fails to run, the app's startup log is reported."""
    log_path = tmp_path / "base_path/logs/first-app.startup.log"

    # The app writes a startup log, then fails to run.
    def fail_to_stream(app, **kwargs):
        create_file(log_path, "CHECKPOINT: interpreter started\nBoom!")
        raise BriefcaseCommandError("Problem running app first-app (return code 1).")

    run_command._stream_app_logs.side_effect = fail_to_stream

    with pytest.raises(BriefcaseCommandError, match=r"return code 1"):
        run_command.run_app(first_app_config, passthrough=[])

    # The contents of the startup log were surfaced to the user.
    output = capsys.readouterr().out
    assert "App startup diagnostics" in output
    assert "CHECKPOINT: interpreter started" in output
    assert "Boom!" in output


def test_startup_log_not_reported_on_success(
    run_command,
    first_app_config,
    tmp_path,
    capsys,
):
    """If the app runs successfully, the startup log isn't reported."""
    log_path = tmp_path / "base_path/logs/first-app.startup.log"

    def stream_and_succeed(app, **kwargs):
        create_file(log_path, "CHECKPOINT: interpreter started")

    run_command._stream_app_logs.side_effect = stream_and_succeed

    run_command.run_app(first_app_config, passthrough=[])

    assert "CHECKPOINT" not in capsys.readouterr().out


def test_empty_startup_log_not_reported(
    run_command,
    first_app_config,
    tmp_path,
    capsys,
):
    """An empty startup log doesn't add noise to the error report."""
    log_path = tmp_path / "base_path/logs/first-app.startup.log"

    def fail_to_stream(app, **kwargs):
        create_file(log_path, "   \n")
        raise BriefcaseCommandError("Problem running app first-app (return code 1).")

    run_command._stream_app_logs.side_effect = fail_to_stream

    with pytest.raises(BriefcaseCommandError, match=r"return code 1"):
        run_command.run_app(first_app_config, passthrough=[])

    assert "App startup diagnostics" not in capsys.readouterr().out


def test_missing_startup_log_on_failure(run_command, first_app_config, capsys):
    """If the app didn't write a startup log, a warning is reported."""
    run_command._stream_app_logs.side_effect = BriefcaseCommandError(
        "Problem running app first-app (return code 1)."
    )

    with pytest.raises(BriefcaseCommandError, match=r"return code 1"):
        run_command.run_app(first_app_config, passthrough=[])

    assert "Unable to read app startup diagnostics" in capsys.readouterr().out
