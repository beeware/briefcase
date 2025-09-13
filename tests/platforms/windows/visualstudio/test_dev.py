import subprocess
import sys
from unittest import mock

import pytest

from briefcase.integrations.subprocess import Subprocess
from briefcase.integrations.virtual_environment import VenvContext
from briefcase.platforms.windows.visualstudio import WindowsVisualStudioDevCommand


@pytest.fixture
def dev_command(dummy_console, tmp_path):
    command = WindowsVisualStudioDevCommand(
        console=dummy_console,
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )
    command.tools.home_path = tmp_path / "home"
    command.tools.subprocess = mock.MagicMock(spec_set=Subprocess)
    command._stream_app_logs = mock.MagicMock()
    return command


@pytest.fixture
def noop_venv() -> VenvContext:
    """Create a no-op venv mock for tests that require a venv parameter."""
    mock_venv = mock.MagicMock(spec=VenvContext)
    mock_venv.run.return_value = mock.MagicMock()
    mock_venv.check_output.return_value = ""
    mock_venv.Popen.return_value = mock.MagicMock()
    mock_venv.executable = "/mock/venv/Scripts/python.exe"
    return mock_venv


def test_dev_visualstudio_app_starts(
    dev_command, first_app_config, tmp_path, noop_venv
):
    """A Windows Visual Studio app can be started in development mode using Python."""
    log_popen = mock.MagicMock()
    noop_venv.Popen.return_value = log_popen

    # Run the dev command
    dev_command.run_dev_app(first_app_config, env={}, venv=noop_venv, passthrough=[])

    # Extract the actual Popen call arguments
    popen_args, popen_kwargs = noop_venv.Popen.call_args

    # Verify that Python is used
    assert popen_args[0][0] == sys.executable

    # Check that the app's module name is in the run command
    assert "run_module" in popen_args[0][2]
    assert first_app_config.module_name in popen_args[0][2]

    # Common subprocess parameters
    assert popen_kwargs["cwd"] == tmp_path / "home"
    assert popen_kwargs["encoding"] == "UTF-8"
    assert popen_kwargs["stdout"] == subprocess.PIPE
    assert popen_kwargs["stderr"] == subprocess.STDOUT
    assert popen_kwargs["bufsize"] == 1

    # Verify log streaming
    dev_command._stream_app_logs.assert_called_once_with(
        first_app_config,
        popen=log_popen,
        clean_output=False,
    )
