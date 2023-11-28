import os
import sys
from unittest.mock import MagicMock

import pytest

from briefcase.console import Console, Log
from briefcase.integrations.docker import DockerAppContext
from briefcase.integrations.subprocess import Subprocess
from briefcase.platforms.linux.appimage import LinuxAppImageOpenCommand

from ...utils import create_file


@pytest.fixture
def open_command(tmp_path):
    command = LinuxAppImageOpenCommand(
        logger=Log(),
        console=Console(),
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )
    command.tools.os = MagicMock(spec_set=os)

    # Mock x86_64 for linuxdeploy verification
    command.tools.host_arch = "x86_64"

    # Store the underlying subprocess instance
    command._subprocess = MagicMock(spec_set=Subprocess)
    command.tools.subprocess = command._subprocess

    # Mock existence of linuxdeploy in tools
    create_file(
        command.tools.base_path / "linuxdeploy-x86_64.AppImage",
        content="",
    )

    return command


@pytest.mark.skipif(
    sys.platform == "win32",
    reason="Windows paths aren't converted in Docker context",
)
def test_open_docker(open_command, first_app_config, tmp_path):
    """Open starts a docker session by default."""

    # Enable docker
    open_command.use_docker = True

    # Provide Docker app context
    open_command.tools[first_app_config].app_context = DockerAppContext(
        tools=open_command.tools,
        app=first_app_config,
    )
    open_command.tools[first_app_config].app_context.prepare(
        image_tag=f"briefcase/com.example.first-app:py3.{sys.version_info.minor}",
        dockerfile_path=tmp_path
        / "base_path"
        / "build"
        / "first-app"
        / "linux"
        / "appimage"
        / "Dockerfile",
        app_base_path=tmp_path / "base_path",
        host_bundle_path=tmp_path
        / "base_path"
        / "build"
        / "first-app"
        / "linux"
        / "appimage",
        host_data_path=tmp_path / "briefcase",
        python_version=f"3.{sys.version_info.minor}",
    )
    # Clear out any calls recorded during preparation
    open_command._subprocess.run.reset_mock()

    # Create the desktop file that would be in the project folder.
    create_file(
        open_command.project_path(first_app_config)
        / "First App.AppDir"
        / "com.example.firstapp.desktop",
        "FreeDesktop file",
    )

    # Open the app
    open_command.open_app(first_app_config)

    # The docker session was started
    open_command._subprocess.run.assert_called_once_with(
        [
            "docker",
            "run",
            "--rm",
            "-it",
            "--volume",
            f"{open_command.base_path}/build/first-app/linux/appimage:/app:z",
            "--volume",
            f"{open_command.data_path}:/briefcase:z",
            f"briefcase/com.example.first-app:py3.{sys.version_info.minor}",
        ],
        stream_output=False,
    )


@pytest.mark.skipif(sys.platform != "linux", reason="Linux specific test")
def test_open_no_docker_linux(open_command, first_app_config, tmp_path):
    """On Linux, Open runs `xdg-open` on the project folder if we specify --no-
    docker."""
    # Create the desktop file that would be in the project folder.
    create_file(
        open_command.project_path(first_app_config)
        / "First App.AppDir"
        / "com.example.firstapp.desktop",
        "FreeDesktop file",
    )

    # Disable docker
    open_command.use_docker = False

    open_command(first_app_config)

    open_command.tools.subprocess.Popen.assert_called_once_with(
        [
            "xdg-open",
            tmp_path / "base_path/build/first-app/linux/appimage",
        ]
    )


@pytest.mark.skipif(sys.platform != "darwin", reason="macOS specific test")
def test_open_no_docker_macOS(open_command, first_app_config, tmp_path):
    """On macOS, Open runs `open` on the project folder if we specify --no-docker."""
    # Create the desktop file that would be in the project folder.
    create_file(
        open_command.project_path(first_app_config)
        / "First App.AppDir"
        / "com.example.firstapp.desktop",
        "FreeDesktop file",
    )

    # Disable docker
    open_command.use_docker = False

    open_command(first_app_config)

    open_command.tools.subprocess.Popen.assert_called_once_with(
        [
            "open",
            tmp_path / "base_path/build/first-app/linux/appimage",
        ]
    )
