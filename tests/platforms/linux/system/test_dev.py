import subprocess
import sys
from pathlib import Path
from unittest import mock

import pytest

from briefcase.integrations.subprocess import Subprocess
from briefcase.platforms.linux.system import LinuxSystemDevCommand

from .test_run import mock_linux_env


@pytest.fixture
def dev_command(monkeypatch, dummy_console, first_app, tmp_path):
    command = LinuxSystemDevCommand(
        console=dummy_console,
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
        apps={"app": first_app},
    )

    # Default to running on Linux
    command.tools.host_os = "Linux"

    # Set the host architecture for test purposes.
    command.tools.host_arch = "wonky"

    mock_linux_env(command, tmp_path, monkeypatch)

    (tmp_path / "base_path/src").mkdir(parents=True)

    command.tools.home_path = tmp_path / "home"
    command.tools.subprocess = mock.MagicMock(spec_set=Subprocess)
    command._stream_app_logs = mock.MagicMock()
    return command


def test_dev_system_app_starts(dev_command, first_app, tmp_path):
    """A Linux system app can be started in development mode."""
    log_popen = mock.MagicMock()
    dev_command.tools.subprocess.Popen.return_value = log_popen

    dev_command.verify_system_packages = mock.MagicMock()

    # Parse the command line
    dev_command.parse_options([])

    # The command runs without error
    dev_command()

    # Running dev will create the dev environment; this will verify system packages.
    dev_command.verify_system_packages.assert_called_once_with(first_app)

    # The app was started with streamed logs
    popen_args, popen_kwargs = dev_command.tools.subprocess.Popen.call_args

    # Check Python executable isn't the system executable.
    # It should be a venv in the base path.
    assert popen_args[0][0] != sys.executable
    assert (
        Path(popen_args[0][0]).parent.parent.parent
        == dev_command.base_path / ".briefcase/first-app"
    )
    assert Path(popen_args[0][0]).parts[-3].startswith("dev.cpython-")
    assert Path(popen_args[0][0]).parts[-2] == (
        "Scripts" if sys.platform == "win32" else "bin"
    )

    # Check that module name is in the inline Python command
    assert "run_module" in popen_args[0][2]
    assert first_app.module_name in popen_args[0][2]

    assert popen_kwargs["cwd"] == tmp_path / "home"
    assert popen_kwargs["encoding"] == "UTF-8"
    assert popen_kwargs["stdout"] == subprocess.PIPE
    assert popen_kwargs["stderr"] == subprocess.STDOUT
    assert popen_kwargs["bufsize"] == 1

    dev_command._stream_app_logs.assert_called_once_with(
        first_app,
        popen=log_popen,
        clean_output=False,
    )
