import sys
from unittest.mock import MagicMock

import pytest

from briefcase.console import Console, Log
from briefcase.exceptions import BriefcaseCommandError
from briefcase.integrations.docker import Docker
from briefcase.integrations.subprocess import Subprocess
from briefcase.platforms.linux.appimage import LinuxAppImageCreateCommand


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
    assert getattr(command.tools, "docker", "MISSING") == "MISSING"


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


def test_verify_linux_docker(tmp_path, first_app_config):
    """If Docker is enabled on Linux, the Docker alias is set."""

    class TestLinuxAppImageCreateCommand(LinuxAppImageCreateCommand):
        @property
        def python_version_tag(self):
            return "3.X"

    command = TestLinuxAppImageCreateCommand(
        logger=Log(),
        console=Console(),
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )

    command.tools.host_os = "Linux"
    command.use_docker = True

    # Mock the existence of Docker.
    command.tools.subprocess = MagicMock(spec_set=Subprocess)
    command.tools.subprocess.check_output.side_effect = [
        "Docker version 19.03.8, build afacb8b\n",
        "docker info return value",
    ]
    command.tools.os = MagicMock()
    # Mock user and group IDs for docker image
    command.tools.os.getuid.return_value = "37"
    command.tools.os.getgid.return_value = "42"

    # Verify the tools
    command.verify_tools()
    command.verify_app_tools(app=first_app_config)

    # The Docker wrapper is set.
    assert isinstance(command.tools.docker, Docker)

    # Docker image is prepared.
    command.tools.subprocess.run.assert_called_with(
        [
            "docker",
            "build",
            "--progress",
            "plain",
            "--tag",
            "briefcase/com.example.first-app:py3.X",
            "--file",
            tmp_path / "base_path" / "linux" / "appimage" / "First App" / "Dockerfile",
            "--build-arg",
            "PY_VERSION=3.X",
            "--build-arg",
            "SYSTEM_REQUIRES=",
            "--build-arg",
            "HOST_UID=37",
            "--build-arg",
            "HOST_GID=42",
            tmp_path / "base_path" / "src",
        ],
        check=True,
    )


def test_verify_non_linux_docker(tmp_path, first_app_config):
    """If Docker is enabled on non-Linux, the Docker alias is set."""

    class TestLinuxAppImageCreateCommand(LinuxAppImageCreateCommand):
        @property
        def python_version_tag(self):
            return "3.X"

    command = TestLinuxAppImageCreateCommand(
        logger=Log(),
        console=Console(),
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )
    command.tools.host_os = "WeirdOS"
    command.use_docker = True

    # Mock the existence of Docker.
    command.tools.subprocess = MagicMock(spec_set=Subprocess)
    command.tools.subprocess.check_output.side_effect = [
        "Docker version 19.03.8, build afacb8b\n",
        "docker info return value",
    ]
    command.tools.os = MagicMock()
    # Mock user and group IDs for docker image
    command.tools.os.getuid.return_value = "37"
    command.tools.os.getgid.return_value = "42"

    # Verify the tools
    command.verify_tools()
    command.verify_app_tools(app=first_app_config)

    # The Docker wrapper is set.
    assert isinstance(command.tools.docker, Docker)

    # Docker image is prepared.
    command.tools.subprocess.run.assert_called_with(
        [
            "docker",
            "build",
            "--progress",
            "plain",
            "--tag",
            "briefcase/com.example.first-app:py3.X",
            "--file",
            tmp_path / "base_path" / "linux" / "appimage" / "First App" / "Dockerfile",
            "--build-arg",
            "PY_VERSION=3.X",
            "--build-arg",
            "SYSTEM_REQUIRES=",
            "--build-arg",
            "HOST_UID=37",
            "--build-arg",
            "HOST_GID=42",
            tmp_path / "base_path" / "src",
        ],
        check=True,
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
