import sys
from unittest.mock import MagicMock

import pytest

from briefcase.console import Console, Log
from briefcase.exceptions import BriefcaseCommandError
from briefcase.integrations.docker import Docker, DockerAppContext
from briefcase.integrations.subprocess import Subprocess
from briefcase.platforms.linux.appimage import (
    LinuxAppImageBuildCommand,
    LinuxAppImageCreateCommand,
)


def test_binary_path(first_app_config, tmp_path):
    command = LinuxAppImageCreateCommand(
        logger=Log(),
        console=Console(),
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )
    # Force the architecture to x86_64 for test purposes.
    command.tools.host_arch = "x86_64"
    binary_path = command.binary_path(first_app_config)

    assert (
        binary_path
        == tmp_path / "base_path" / "linux" / "First_App-0.0.1-x86_64.AppImage"
    )


def test_distribution_path(first_app_config, tmp_path):
    command = LinuxAppImageCreateCommand(
        logger=Log(),
        console=Console(),
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )
    # Force the architecture to x86_64 for test purposes.
    command.tools.host_arch = "x86_64"
    distribution_path = command.distribution_path(first_app_config, "appimage")

    assert (
        distribution_path
        == tmp_path / "base_path" / "linux" / "First_App-0.0.1-x86_64.AppImage"
    )


def test_docker_image_tag(first_app_config, tmp_path):
    command = LinuxAppImageCreateCommand(
        logger=Log(),
        console=Console(),
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )

    image_tag = command.docker_image_tag(first_app_config)

    assert image_tag == f"briefcase/com.example.first-app:py3.{sys.version_info.minor}"


def test_docker_image_tag_uppercase_name(uppercase_app_config, tmp_path):
    command = LinuxAppImageCreateCommand(
        logger=Log(),
        console=Console(),
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )

    image_tag = command.docker_image_tag(uppercase_app_config)

    assert image_tag == f"briefcase/com.example.first-app:py3.{sys.version_info.minor}"


def test_verify_linux_no_docker(tmp_path, first_app_config):
    """If Docker is disabled on Linux, the app_context is Subprocess."""
    command = LinuxAppImageCreateCommand(
        logger=Log(),
        console=Console(),
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )
    command.tools.host_os = "Linux"
    command.use_docker = False

    # Verify the tools
    command.verify_tools()
    command.verify_app_tools(app=first_app_config)

    # No error and Subprocess is used.
    assert isinstance(command.tools[first_app_config].app_context, Subprocess)
    # Docker is not verified.
    assert not hasattr(command.tools, "docker")


def test_verify_non_linux_no_docker(tmp_path):
    """If Docker is disabled on non-Linux, an error is raised."""
    command = LinuxAppImageCreateCommand(
        logger=Log(),
        console=Console(),
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )
    command.tools.host_os = "WeirdOS"
    command.use_docker = False

    # Verify the Docker tool
    with pytest.raises(
        BriefcaseCommandError,
        match="Linux AppImages can only be generated on Linux without Docker",
    ):
        command.verify_tools()


def test_verify_linux_docker(tmp_path, first_app_config, monkeypatch):
    """If Docker is enabled on Linux, the Docker alias is set."""
    command = LinuxAppImageCreateCommand(
        logger=Log(),
        console=Console(),
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )
    command.tools.host_os = "Linux"
    command.use_docker = True

    # Mock Docker tool verification
    Docker.verify = MagicMock()
    DockerAppContext.verify = MagicMock()

    # Verify the tools
    command.verify_tools()
    command.verify_app_tools(app=first_app_config)

    # Docker and Docker app context are verified
    Docker.verify.assert_called_with(tools=command.tools)
    DockerAppContext.verify.assert_called_with(
        tools=command.tools,
        app=first_app_config,
        image_tag=f"briefcase/com.example.first-app:py3.{sys.version_info.minor}",
        dockerfile_path=tmp_path
        / "base_path"
        / "linux"
        / "appimage"
        / "First App"
        / "Dockerfile",
        app_base_path=tmp_path / "base_path",
        host_platform_path=tmp_path / "base_path" / "linux",
        host_data_path=tmp_path / "briefcase",
        python_version=f"3.{sys.version_info.minor}",
    )


def test_verify_non_linux_docker(tmp_path, first_app_config):
    """If Docker is enabled on non-Linux, the Docker alias is set."""
    command = LinuxAppImageCreateCommand(
        logger=Log(),
        console=Console(),
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )
    command.tools.host_os = "WeirdOS"
    command.use_docker = True

    # Mock Docker tool verification
    Docker.verify = MagicMock()
    DockerAppContext.verify = MagicMock()

    # Verify the tools
    command.verify_tools()
    command.verify_app_tools(app=first_app_config)

    # Docker and Docker app context are verified
    Docker.verify.assert_called_with(tools=command.tools)
    DockerAppContext.verify.assert_called_with(
        tools=command.tools,
        app=first_app_config,
        image_tag=f"briefcase/com.example.first-app:py3.{sys.version_info.minor}",
        dockerfile_path=tmp_path
        / "base_path"
        / "linux"
        / "appimage"
        / "First App"
        / "Dockerfile",
        app_base_path=tmp_path / "base_path",
        host_platform_path=tmp_path / "base_path" / "linux",
        host_data_path=tmp_path / "briefcase",
        python_version=f"3.{sys.version_info.minor}",
    )


def test_verify_windows_docker(tmp_path):
    """Docker cannot currently be used on Windows due to path issues."""
    command = LinuxAppImageCreateCommand(
        logger=Log(),
        console=Console(),
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )
    command.tools.host_os = "Windows"
    command.use_docker = True

    # Verify the tools
    with pytest.raises(BriefcaseCommandError):
        command.verify_tools()


def test_clone_options(tmp_path):
    """Docker options are cloned."""
    build_command = LinuxAppImageBuildCommand(
        logger=Log(),
        console=Console(),
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )
    build_command.use_docker = True

    create_command = build_command.create_command

    # Confirm the use_docker option has been cloned.
    assert create_command.is_clone
    assert create_command.use_docker
