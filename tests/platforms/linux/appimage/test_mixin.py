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
    command.host_arch = 'x86_64'
    binary_path = command.binary_path(first_app_config)

    assert binary_path == tmp_path / 'linux' / 'First_App-0.0.1-x86_64.AppImage'


def test_distribution_path(first_app_config, tmp_path):
    command = LinuxAppImageCreateCommand(base_path=tmp_path)
    # Force the architecture to x86_64 for test purposes.
    command.host_arch = 'x86_64'
    distribution_path = command.distribution_path(first_app_config, 'appimage')

    assert distribution_path == tmp_path / 'linux' / 'First_App-0.0.1-x86_64.AppImage'


def test_docker_image_tag(first_app_config, tmp_path):
    command = LinuxAppImageCreateCommand(base_path=tmp_path)

    image_tag = command.docker_image_tag(first_app_config)

    assert image_tag == 'briefcase/com.example.first-app:py3.{minor}'.format(
        minor=sys.version_info.minor
    )


def test_docker_image_tag_uppercase_name(uppercase_app_config, tmp_path):
    command = LinuxAppImageCreateCommand(base_path=tmp_path)

    image_tag = command.docker_image_tag(uppercase_app_config)

    assert image_tag == 'briefcase/com.example.first-app:py3.{minor}'.format(
        minor=sys.version_info.minor
    )


def test_dockerize(first_app_config, tmp_path):
    command = LinuxAppImageCreateCommand(base_path=tmp_path)
    command.Docker = Docker
    command.use_docker = True

    # Before dockerization, subprocess is native
    assert type(command.subprocess) == Subprocess

    with command.dockerize(first_app_config):
        # During dockerization, subprocess is a container
        assert type(command.subprocess) == Docker

    # After dockerization, subprocess is native
    assert type(command.subprocess) == Subprocess


def test_dockerize_nodocker(first_app_config, tmp_path):
    "If docker is not in use, dockerize() is a no-op."
    command = LinuxAppImageCreateCommand(base_path=tmp_path)
    command.Docker = Docker
    command.use_docker = False

    # Before dockerization, subprocess is native
    assert type(command.subprocess) == Subprocess

    with command.dockerize(first_app_config):
        # During dockerization, subprocess is *still* native
        assert type(command.subprocess) == Subprocess

    # After dockerization, subprocess is native
    assert type(command.subprocess) == Subprocess


def test_verify_linux_no_docker(tmp_path):
    "If Docker is disabled on Linux, the Docker alias is not set"
    command = LinuxAppImageCreateCommand(base_path=tmp_path)
    command.host_os = "Linux"
    command.use_docker = False

    # Verify the tools
    command.verify_tools()

    # No error, but no Docker wrapper either.
    assert command.Docker is None


def test_verify_non_linux_no_docker(tmp_path):
    "If Docker is disabled on non-Linux, an error is raised"
    command = LinuxAppImageCreateCommand(base_path=tmp_path)
    command.host_os = "WeirdOS"
    command.use_docker = False
    command.verbosity = 0

    # Verify the tools
    with pytest.raises(BriefcaseCommandError):
        command.verify_tools()


def test_verify_linux_docker(tmp_path):
    "If Docker is enabled on Linux, the Docker alias is set"
    command = LinuxAppImageCreateCommand(base_path=tmp_path)
    command.host_os = "Linux"
    command.use_docker = True
    command.verbosity = 0
    # Mock the existence of Docker.
    command.subprocess = MagicMock()
    command.subprocess.check_output.return_value = "Docker version 19.03.8, build afacb8b\n"

    # Verify the tools
    command.verify_tools()

    # The Docker wrapper is set.
    assert command.Docker == Docker


def test_verify_non_linux_docker(tmp_path):
    "If Docker is enabled on non-Linux, the Docker alias is set"
    command = LinuxAppImageCreateCommand(base_path=tmp_path)
    command.host_os = "WierdOS"
    command.use_docker = True
    command.verbosity = 0
    # Mock the existence of Docker.
    command.subprocess = MagicMock()
    command.subprocess.check_output.return_value = "Docker version 19.03.8, build afacb8b\n"

    # Verify the tools
    command.verify_tools()

    # The Docker wrapper is set.
    assert command.Docker == Docker


def test_verify_windows_docker(tmp_path):
    "Docker cannot currently be used on Windows due to path issues"
    command = LinuxAppImageCreateCommand(base_path=tmp_path)
    command.host_os = "Windows"
    command.use_docker = True
    command.verbosity = 0

    # Verify the tools
    with pytest.raises(BriefcaseCommandError):
        command.verify_tools()
