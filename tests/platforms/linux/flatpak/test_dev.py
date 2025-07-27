import subprocess
import sys
from unittest import mock


def test_flatpak_dev_starts(dev_command, first_app_config, tmp_path):
    """A Flatpak app can be started in development mode using Python."""
    log_popen = mock.MagicMock()
    dev_command.tools.subprocess.Popen.return_value = log_popen

    dev_command.run_dev_app(first_app_config, env={}, passthrough=[])

    popen_args, popen_kwargs = dev_command.tools.subprocess.Popen.call_args

    # Check that Python executable is used
    assert popen_args[0][0] == sys.executable
    assert "run_module" in popen_args[0][2]
    assert first_app_config.module_name in popen_args[0][2]

    # Validate subprocess settings
    assert popen_kwargs["cwd"] == tmp_path / "home"
    assert popen_kwargs["encoding"] == "UTF-8"
    assert popen_kwargs["stdout"] == subprocess.PIPE
    assert popen_kwargs["stderr"] == subprocess.STDOUT
    assert popen_kwargs["bufsize"] == 1

    dev_command._stream_app_logs.assert_called_once_with(
        first_app_config, popen=log_popen, clean_output=False
    )
