import sys
from unittest.mock import MagicMock

import pytest

from briefcase.exceptions import BriefcaseCommandError
from briefcase.integrations.docker import Docker
from briefcase.integrations.subprocess import Subprocess
from briefcase.platforms.linux.appimage import LinuxAppImageCreateCommand


def test_binary_path(first_app_config, tmp_path):
    command = LinuxAppImageCreateCommand(base_path=tmp_path)
    # Force the architecture to x86_64 for test purposes.
    command.host_arch = "x86_64"
    binary_path = command.binary_path(first_app_config)

    assert binary_path == tmp_path / "linux" / "First_App-0.0.1-x86_64.AppImage"


def test_distribution_path(first_app_config, tmp_path):
    command = LinuxAppImageCreateCommand(base_path=tmp_path)
    # Force the architecture to x86_64 for test purposes.
    command.host_arch = "x86_64"
    distribution_path = command.distribution_path(first_app_config, "appimage")

    assert distribution_path == tmp_path / "linux" / "First_App-0.0.1-x86_64.AppImage"


def test_docker_image_tag(first_app_config, tmp_path):
    command = LinuxAppImageCreateCommand(base_path=tmp_path)

    image_tag = command.docker_image_tag(first_app_config)

    assert image_tag == f"briefcase/com.example.first-app:py3.{sys.version_info.minor}"


def test_docker_image_tag_uppercase_name(uppercase_app_config, tmp_path):
    command = LinuxAppImageCreateCommand(base_path=tmp_path)

    image_tag = command.docker_image_tag(uppercase_app_config)

    assert image_tag == f"briefcase/com.example.first-app:py3.{sys.version_info.minor}"


def test_prepare_build_subprocess(first_app_config, tmp_path):
    """Build subprocess is a Docker proxy."""
    command = LinuxAppImageCreateCommand(base_path=tmp_path)
    command.Docker = Docker
    command.Docker.prepare = MagicMock()
    command.use_docker = True

    build_subprocess = command.prepare_build_environment(first_app_config)

    assert type(build_subprocess) == Docker


def test_prepare_build_subprocess_no_docker(first_app_config, tmp_path):
    """Build subprocess remains the subprocess for the local environment."""
    command = LinuxAppImageCreateCommand(base_path=tmp_path)
    command.Docker = Docker
    command.use_docker = False

    build_subprocess = command.prepare_build_environment(first_app_config)

    assert type(build_subprocess) == Subprocess


def test_verify_linux_no_docker(tmp_path):
    """If Docker is disabled on Linux, the Docker alias is not set."""
    command = LinuxAppImageCreateCommand(base_path=tmp_path)
    command.host_os = "Linux"
    command.use_docker = False

    # Verify the tools
    command.verify_tools()

    # No error, but no Docker wrapper either.
    assert command.Docker is None


def test_verify_non_linux_no_docker(tmp_path):
    """If Docker is disabled on non-Linux, an error is raised."""
    command = LinuxAppImageCreateCommand(base_path=tmp_path)
    command.host_os = "WeirdOS"
    command.use_docker = False

    # Verify the tools
    with pytest.raises(BriefcaseCommandError):
        command.verify_tools()


def test_verify_linux_docker(tmp_path):
    """If Docker is enabled on Linux, the Docker alias is set."""
    command = LinuxAppImageCreateCommand(base_path=tmp_path)
    command.host_os = "Linux"
    command.use_docker = True
    # Mock the existence of Docker.
    command.subprocess = MagicMock()
    command.subprocess.check_output.return_value = (
        "Docker version 19.03.8, build afacb8b\n"
    )

    # Verify the tools
    command.verify_tools()

    # The Docker wrapper is set.
    assert command.Docker == Docker


def test_verify_non_linux_docker(tmp_path):
    """If Docker is enabled on non-Linux, the Docker alias is set."""
    command = LinuxAppImageCreateCommand(base_path=tmp_path)
    command.host_os = "WierdOS"
    command.use_docker = True
    # Mock the existence of Docker.
    command.subprocess = MagicMock()
    command.subprocess.check_output.return_value = (
        "Docker version 19.03.8, build afacb8b\n"
    )

    # Verify the tools
    command.verify_tools()

    # The Docker wrapper is set.
    assert command.Docker == Docker


def test_verify_windows_docker(tmp_path):
    """Docker cannot currently be used on Windows due to path issues."""
    command = LinuxAppImageCreateCommand(base_path=tmp_path)
    command.host_os = "Windows"
    command.use_docker = True

    # Verify the tools
    with pytest.raises(BriefcaseCommandError):
        command.verify_tools()
