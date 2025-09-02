# The run command inherits most of its behavior from the common base
# implementation. Do a surface-level verification here, but the app
# tests provide the actual test coverage.
import json
import subprocess
from unittest import mock

import pytest

from briefcase.console import Console
from briefcase.integrations.subprocess import Subprocess
from briefcase.platforms.windows.visualstudio import WindowsVisualStudioRunCommand


@pytest.fixture
def run_command(tmp_path):
    command = WindowsVisualStudioRunCommand(
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
    run_command.run_app(
        first_app_config, debugger_host=None, debugger_port=None, passthrough=[]
    )

    # Popen was called
    run_command.tools.subprocess.Popen.assert_called_with(
        [
            tmp_path
            / "base_path/build/first-app/windows/visualstudio/x64/Release/First App.exe"
        ],
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


def test_run_app_with_args(run_command, first_app_config, tmp_path):
    """A windows Visual Studio project app can be started with args."""

    # Set up the log streamer to return a known stream with a good returncode
    log_popen = mock.MagicMock()
    run_command.tools.subprocess.Popen.return_value = log_popen

    # Run the app with args
    run_command.run_app(
        first_app_config,
        debugger_host=None,
        debugger_port=None,
        passthrough=["foo", "--bar"],
    )

    # Popen was called
    run_command.tools.subprocess.Popen.assert_called_with(
        [
            tmp_path
            / "base_path/build/first-app/windows/visualstudio/x64/Release/First App.exe",
            "foo",
            "--bar",
        ],
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


def test_run_app_test_mode(run_command, first_app_config, tmp_path):
    """A windows Visual Studio project app can be started in test mode."""
    first_app_config.test_mode = True

    # Set up the log streamer to return a known stream with a good returncode
    log_popen = mock.MagicMock()
    run_command.tools.subprocess.Popen.return_value = log_popen

    # Run the app in test mode
    run_command.run_app(
        first_app_config, debugger_host=None, debugger_port=None, passthrough=[]
    )

    # Popen was called
    run_command.tools.subprocess.Popen.assert_called_with(
        [
            tmp_path
            / "base_path/build/first-app/windows/visualstudio/x64/Release/First App.exe"
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


def test_run_app_test_mode_with_args(run_command, first_app_config, tmp_path):
    """A windows Visual Studio project app can be started in test mode with args."""
    first_app_config.test_mode = True

    # Set up the log streamer to return a known stream with a good returncode
    log_popen = mock.MagicMock()
    run_command.tools.subprocess.Popen.return_value = log_popen

    # Run the app with args
    run_command.run_app(
        first_app_config,
        debugger_host=None,
        debugger_port=None,
        passthrough=["foo", "--bar"],
    )

    # Popen was called
    run_command.tools.subprocess.Popen.assert_called_with(
        [
            tmp_path
            / "base_path/build/first-app/windows/visualstudio/x64/Release/First App.exe",
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


def test_run_app_debugger(run_command, first_app_config, tmp_path, dummy_debugger):
    """A windows Visual Studio project app can be started in debug mode."""
    first_app_config.debugger = dummy_debugger

    # Set up the log streamer to return a known stream with a good returncode
    log_popen = mock.MagicMock()
    run_command.tools.subprocess.Popen.return_value = log_popen

    # Run the app in test mode
    run_command.run_app(
        first_app_config,
        debugger_host="somehost",
        debugger_port=9999,
        passthrough=[],
    )

    # Popen was called
    run_command.tools.subprocess.Popen.assert_called_with(
        [
            tmp_path
            / "base_path/build/first-app/windows/visualstudio/x64/Release/First App.exe"
        ],
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
                    "app_path_mappings": {
                        "device_sys_path_regex": "app$",
                        "device_subfolders": ["first_app"],
                        "host_folders": [str(tmp_path / "base_path/src/first_app")],
                    },
                    "app_packages_path_mappings": None,
                }
            )
        },
    )

    # The streamer was started
    run_command._stream_app_logs.assert_called_once_with(
        first_app_config,
        popen=log_popen,
        clean_output=False,
    )
