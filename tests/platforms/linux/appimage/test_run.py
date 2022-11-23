import os
import subprocess
from unittest import mock

import pytest

from briefcase.console import Console, Log
from briefcase.exceptions import BriefcaseCommandError
from briefcase.integrations.subprocess import Subprocess
from briefcase.platforms.linux.appimage import LinuxAppImageRunCommand


@pytest.fixture
def run_command(tmp_path):
    command = LinuxAppImageRunCommand(
        logger=Log(),
        console=Console(),
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )
    command.tools.home_path = tmp_path / "home"

    # Set the host architecture for test purposes.
    command.tools.host_arch = "wonky"

    command.tools.subprocess = mock.MagicMock(spec_set=Subprocess)

    command._stream_app_logs = mock.MagicMock()

    return command


def test_verify_linux(run_command):
    """A linux App can be started on linux."""
    run_command.use_docker = True
    run_command.tools.host_os = "Linux"

    # Mock the existence of Docker.
    run_command.tools.subprocess.check_output.return_value = (
        "Docker version 19.03.8, build afacb8b\n"
    )

    run_command.verify_tools()


def test_verify_non_linux(run_command):
    """A linux App cannot be started on linux, even if Docker is enabled."""
    run_command.use_docker = True
    run_command.tools.host_os = "WierdOS"

    # Mock the existence of Docker.
    run_command.tools.subprocess.check_output.return_value = (
        "Docker version 19.03.8, build afacb8b\n"
    )

    with pytest.raises(
        BriefcaseCommandError, match="AppImages can only be executed on Linux"
    ):
        run_command.verify_tools()


def test_run_app(run_command, first_app_config, tmp_path):
    """A linux App can be started."""
    # Set up the log streamer to return a known stream
    log_popen = mock.MagicMock()
    run_command.tools.subprocess.Popen.return_value = log_popen

    # Run the app
    run_command.run_app(first_app_config, test_mode=False)

    # The process was started
    run_command.tools.subprocess.Popen.assert_called_with(
        [
            os.fsdecode(
                tmp_path / "base_path" / "linux" / "First_App-0.0.1-wonky.AppImage"
            )
        ],
        cwd=tmp_path / "home",
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=1,
    )

    # The streamer was started
    run_command._stream_app_logs.assert_called_once_with(
        first_app_config,
        popen=log_popen,
        test_mode=False,
        clean_output=False,
    )


def test_run_app_failed(run_command, first_app_config, tmp_path):
    """If there's a problem starting the app, an exception is raised."""
    run_command.tools.subprocess.Popen.side_effect = OSError

    with pytest.raises(OSError):
        run_command.run_app(first_app_config, test_mode=False)

    # The run command was still invoked
    run_command.tools.subprocess.Popen.assert_called_with(
        [
            os.fsdecode(
                tmp_path / "base_path" / "linux" / "First_App-0.0.1-wonky.AppImage"
            )
        ],
        cwd=tmp_path / "home",
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=1,
    )

    # No attempt to stream was made
    run_command._stream_app_logs.assert_not_called()


def test_run_app_test_mode(run_command, first_app_config, tmp_path):
    """A linux App can be started in test mode."""
    # Set up the log streamer to return a known stream
    log_popen = mock.MagicMock()
    run_command.tools.subprocess.Popen.return_value = log_popen

    # Run the app
    run_command.run_app(first_app_config, test_mode=True)

    # The process was started
    run_command.tools.subprocess.Popen.assert_called_with(
        [
            os.fsdecode(
                tmp_path / "base_path" / "linux" / "First_App-0.0.1-wonky.AppImage"
            )
        ],
        cwd=tmp_path / "home",
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=1,
        env={"BRIEFCASE_MAIN_MODULE": "tests.first_app"},
    )

    # The streamer was started
    run_command._stream_app_logs.assert_called_once_with(
        first_app_config,
        popen=log_popen,
        test_mode=True,
        clean_output=False,
    )
