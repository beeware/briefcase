import os
from unittest.mock import MagicMock

import pytest

from briefcase.exceptions import BriefcaseCommandError
from briefcase.platforms.linux.appimage import LinuxAppImageRunCommand


def test_verify_linux(tmp_path):
    """A linux App can be started on linux."""
    command = LinuxAppImageRunCommand(base_path=tmp_path)
    command.use_docker = True
    command.host_os = "Linux"

    # Mock the existence of Docker.
    command.subprocess = MagicMock()
    command.subprocess.check_output.return_value = (
        "Docker version 19.03.8, build afacb8b\n"
    )

    command.verify_tools()


def test_verify_non_linux(tmp_path):
    """A linux App can be started on linux, even if Docker is enabled."""
    command = LinuxAppImageRunCommand(base_path=tmp_path)
    command.use_docker = True
    command.host_os = "WierdOS"

    # Mock the existence of Docker.
    command.subprocess = MagicMock()
    command.subprocess.check_output.return_value = (
        "Docker version 19.03.8, build afacb8b\n"
    )

    with pytest.raises(BriefcaseCommandError):
        command.verify_tools()


def test_run_app(first_app_config, tmp_path):
    """A linux App can be started."""
    command = LinuxAppImageRunCommand(base_path=tmp_path)

    # Set the host architecture for test purposes.
    command.host_arch = "wonky"

    command.subprocess = MagicMock()

    command.run_app(first_app_config)

    command.subprocess.run.assert_called_with(
        [os.fsdecode(tmp_path / "linux" / "First_App-0.0.1-wonky.AppImage")], check=True
    )


def test_run_app_failed(first_app_config, tmp_path):
    """If there's a problem started the app, an exception is raised."""
    command = LinuxAppImageRunCommand(base_path=tmp_path)

    # Set the host architecture for test purposes.
    command.host_arch = "wonky"

    command.subprocess = MagicMock()
    command.subprocess.run.side_effect = BriefcaseCommandError("problem")

    with pytest.raises(BriefcaseCommandError):
        command.run_app(first_app_config)

    # The run command was still invoked, though
    command.subprocess.run.assert_called_with(
        [os.fsdecode(tmp_path / "linux" / "First_App-0.0.1-wonky.AppImage")], check=True
    )
