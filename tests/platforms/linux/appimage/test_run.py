import os
from subprocess import CalledProcessError
from unittest.mock import MagicMock

import pytest

from briefcase.console import Console, Log
from briefcase.exceptions import BriefcaseCommandError
from briefcase.integrations.subprocess import Subprocess
from briefcase.platforms.linux.appimage import LinuxAppImageRunCommand


def test_verify_linux(tmp_path):
    """A linux App can be started on linux."""
    command = LinuxAppImageRunCommand(
        logger=Log(),
        console=Console(),
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )
    command.tools.home_path = tmp_path / "home"
    command.use_docker = True
    command.tools.host_os = "Linux"

    # Mock the existence of Docker.
    command.tools.subprocess = MagicMock(spec_set=Subprocess)
    command.tools.subprocess.check_output.return_value = (
        "Docker version 19.03.8, build afacb8b\n"
    )

    command.verify_tools()


def test_verify_non_linux(tmp_path):
    """A linux App cannot be started on linux, even if Docker is enabled."""
    command = LinuxAppImageRunCommand(
        logger=Log(),
        console=Console(),
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )
    command.tools.home_path = tmp_path / "home"
    command.use_docker = True
    command.tools.host_os = "WierdOS"

    # Mock the existence of Docker.
    command.tools.subprocess = MagicMock(spec_set=Subprocess)
    command.tools.subprocess.check_output.return_value = (
        "Docker version 19.03.8, build afacb8b\n"
    )

    with pytest.raises(
        BriefcaseCommandError, match="AppImages can only be executed on Linux"
    ):
        command.verify_tools()


def test_run_app(first_app_config, tmp_path):
    """A linux App can be started."""
    command = LinuxAppImageRunCommand(
        logger=Log(),
        console=Console(),
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )
    command.tools.home_path = tmp_path / "home"

    # Set the host architecture for test purposes.
    command.tools.host_arch = "wonky"

    command.tools.subprocess = MagicMock(spec_set=Subprocess)

    command.run_app(first_app_config)

    command.tools.subprocess.run.assert_called_with(
        [
            os.fsdecode(
                tmp_path / "base_path" / "linux" / "First_App-0.0.1-wonky.AppImage"
            )
        ],
        cwd=tmp_path / "home",
        check=True,
        stream_output=True,
    )


def test_run_app_failed(first_app_config, tmp_path):
    """If there's a problem started the app, an exception is raised."""
    command = LinuxAppImageRunCommand(
        logger=Log(),
        console=Console(),
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )
    command.tools.home_path = tmp_path / "home"

    # Set the host architecture for test purposes.
    command.tools.host_arch = "wonky"

    command.tools.subprocess = MagicMock(spec_set=Subprocess)
    command.tools.subprocess.run.side_effect = CalledProcessError(
        cmd=["First App.AppImage"], returncode=1
    )

    with pytest.raises(BriefcaseCommandError):
        command.run_app(first_app_config)

    # The run command was still invoked, though
    command.tools.subprocess.run.assert_called_with(
        [
            os.fsdecode(
                tmp_path / "base_path" / "linux" / "First_App-0.0.1-wonky.AppImage"
            )
        ],
        cwd=tmp_path / "home",
        check=True,
        stream_output=True,
    )
