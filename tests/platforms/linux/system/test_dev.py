import subprocess
import sys
from unittest import mock

import pytest

from briefcase.integrations.subprocess import Subprocess
from briefcase.platforms.linux.system import LinuxSystemDevCommand


@pytest.fixture
def dev_command(dummy_console, tmp_path):
    command = LinuxSystemDevCommand(
        console=dummy_console,
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )
    command.tools.home_path = tmp_path / "home"
    command.tools.subprocess = mock.MagicMock(spec_set=Subprocess)
    command._stream_app_logs = mock.MagicMock()
    return command


def test_dev_system_app_starts(dev_command, first_app_config, tmp_path):
    """A Linux system app can be started in development mode."""
    log_popen = mock.MagicMock()
    dev_command.tools.subprocess.Popen.return_value = log_popen

    dev_command.run_dev_app(first_app_config, env={}, passthrough=[])

    popen_args, popen_kwargs = dev_command.tools.subprocess.Popen.call_args

    # Check Python executable
    assert popen_args[0][0] == sys.executable
    # Check that module name is in the inline Python command
    assert "run_module" in popen_args[0][2]
    assert first_app_config.module_name in popen_args[0][2]

    assert popen_kwargs["cwd"] == tmp_path / "home"
    assert popen_kwargs["encoding"] == "UTF-8"
    assert popen_kwargs["stdout"] == subprocess.PIPE
    assert popen_kwargs["stderr"] == subprocess.STDOUT
    assert popen_kwargs["bufsize"] == 1

    dev_command._stream_app_logs.assert_called_once_with(
        first_app_config,
        popen=log_popen,
        clean_output=False,
    )
