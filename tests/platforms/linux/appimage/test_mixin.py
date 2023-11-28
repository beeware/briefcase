import sys
from unittest.mock import MagicMock

import pytest

import briefcase.platforms.linux.appimage
from briefcase.console import Console, Log
from briefcase.integrations.docker import Docker, DockerAppContext
from briefcase.integrations.linuxdeploy import LinuxDeploy
from briefcase.integrations.subprocess import Subprocess
from briefcase.platforms.linux.appimage import (
    LinuxAppImageBuildCommand,
    LinuxAppImageCreateCommand,
)


@pytest.fixture
def create_command(tmp_path):
    command = LinuxAppImageCreateCommand(
        logger=Log(),
        console=Console(),
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )
    # Mock verified linuxdeploy
    command.tools.linuxdeploy = LinuxDeploy(tools=command.tools)
    return command


def test_binary_path(create_command, first_app_config, tmp_path):
    # Force the architecture to x86_64 for test purposes.
    create_command.tools.host_arch = "x86_64"
    binary_path = create_command.binary_path(first_app_config)

    assert (
        binary_path
        == tmp_path
        / "base_path"
        / "build"
        / "first-app"
        / "linux"
        / "appimage"
        / "First_App-0.0.1-x86_64.AppImage"
    )


def test_project_path(create_command, first_app_config, tmp_path):
    """The project path is the bundle path."""
    project_path = create_command.project_path(first_app_config)
    bundle_path = create_command.bundle_path(first_app_config)

    expected_path = tmp_path / "base_path/build/first-app/linux/appimage"
    assert expected_path == project_path == bundle_path


def test_distribution_path(create_command, first_app_config, tmp_path):
    # Force the architecture to x86_64 for test purposes.
    create_command.tools.host_arch = "x86_64"
    distribution_path = create_command.distribution_path(first_app_config)

    assert (
        distribution_path == tmp_path / "base_path/dist/First_App-0.0.1-x86_64.AppImage"
    )


@pytest.mark.parametrize(
    "manylinux, tag",
    [
        (None, "appimage"),
        ("manylinux1", "manylinux1-appimage"),
        ("manylinux_2_28", "manylinux_2_28-appimage"),
    ],
)
def test_docker_image_tag(create_command, first_app_config, manylinux, tag):
    if manylinux:
        first_app_config.manylinux = manylinux

    image_tag = create_command.docker_image_tag(first_app_config)

    assert image_tag == f"briefcase/com.example.first-app:{tag}"


def test_docker_image_tag_uppercase_name(
    create_command,
    uppercase_app_config,
    tmp_path,
):
    image_tag = create_command.docker_image_tag(uppercase_app_config)

    assert image_tag == "briefcase/com.example.first-app:appimage"


def test_verify_linux_no_docker(create_command, first_app_config, tmp_path):
    """If Docker is disabled on Linux, the app_context is Subprocess."""
    create_command.tools.host_os = "Linux"
    create_command.use_docker = False

    # Verify the tools
    create_command.verify_tools()
    create_command.verify_app_tools(app=first_app_config)

    # No error and Subprocess is used.
    assert isinstance(create_command.tools[first_app_config].app_context, Subprocess)
    # Docker is not verified.
    assert not hasattr(create_command.tools, "docker")


def test_verify_linux_docker(create_command, tmp_path, first_app_config, monkeypatch):
    """If Docker is enabled on Linux, the Docker alias is set."""
    create_command.tools.host_os = "Linux"
    create_command.use_docker = True

    # Mock Docker tool verification
    mock__version_compat = MagicMock(spec=Docker._version_compat)
    mock__user_access = MagicMock(spec=Docker._user_access)
    mock__buildx_installed = MagicMock(spec=Docker._buildx_installed)
    mock__is_user_mapping_enabled = MagicMock(spec=Docker._is_user_mapping_enabled)
    monkeypatch.setattr(
        briefcase.platforms.linux.appimage.Docker,
        "_version_compat",
        mock__version_compat,
    )
    monkeypatch.setattr(
        briefcase.platforms.linux.appimage.Docker,
        "_user_access",
        mock__user_access,
    )
    monkeypatch.setattr(
        briefcase.platforms.linux.appimage.Docker,
        "_buildx_installed",
        mock__buildx_installed,
    )
    monkeypatch.setattr(
        briefcase.platforms.linux.appimage.Docker,
        "_is_user_mapping_enabled",
        mock__is_user_mapping_enabled,
    )
    mock_docker_app_context_verify = MagicMock(spec=DockerAppContext.verify)
    monkeypatch.setattr(
        briefcase.platforms.linux.appimage.DockerAppContext,
        "verify",
        mock_docker_app_context_verify,
    )

    # Verify the tools
    create_command.verify_tools()
    create_command.verify_app_tools(app=first_app_config)

    # Docker and Docker app context are verified
    mock__version_compat.assert_called_with(tools=create_command.tools)
    mock__user_access.assert_called_with(tools=create_command.tools)
    mock__buildx_installed.assert_called_with(tools=create_command.tools)
    mock__is_user_mapping_enabled.assert_called_with(None)
    assert isinstance(create_command.tools.docker, Docker)
    mock_docker_app_context_verify.assert_called_with(
        tools=create_command.tools,
        app=first_app_config,
        image_tag="briefcase/com.example.first-app:appimage",
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


def test_verify_non_linux_docker(
    create_command,
    first_app_config,
    monkeypatch,
    tmp_path,
):
    """If Docker is enabled on non-Linux, the Docker alias is set."""
    create_command.tools.host_os = "Darwin"
    create_command.use_docker = True

    # Mock Docker tool verification
    mock__version_compat = MagicMock(spec=Docker._version_compat)
    mock__user_access = MagicMock(spec=Docker._user_access)
    mock__buildx_installed = MagicMock(spec=Docker._buildx_installed)
    mock__is_user_mapping_enabled = MagicMock(spec=Docker._is_user_mapping_enabled)
    monkeypatch.setattr(
        briefcase.platforms.linux.appimage.Docker,
        "_version_compat",
        mock__version_compat,
    )
    monkeypatch.setattr(
        briefcase.platforms.linux.appimage.Docker,
        "_user_access",
        mock__user_access,
    )
    monkeypatch.setattr(
        briefcase.platforms.linux.appimage.Docker,
        "_buildx_installed",
        mock__buildx_installed,
    )
    monkeypatch.setattr(
        briefcase.platforms.linux.appimage.Docker,
        "_is_user_mapping_enabled",
        mock__is_user_mapping_enabled,
    )
    mock_docker_app_context_verify = MagicMock(spec=DockerAppContext.verify)
    monkeypatch.setattr(
        briefcase.platforms.linux.appimage.DockerAppContext,
        "verify",
        mock_docker_app_context_verify,
    )

    # Verify the tools
    create_command.verify_tools()
    create_command.verify_app_tools(app=first_app_config)

    # Docker and Docker app context are verified
    mock__version_compat.assert_called_with(tools=create_command.tools)
    mock__user_access.assert_called_with(tools=create_command.tools)
    mock__buildx_installed.assert_called_with(tools=create_command.tools)
    mock__is_user_mapping_enabled.assert_called_with(None)
    assert isinstance(create_command.tools.docker, Docker)
    mock_docker_app_context_verify.assert_called_with(
        tools=create_command.tools,
        app=first_app_config,
        image_tag="briefcase/com.example.first-app:appimage",
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

    # Confirm the use_docker option has been cloned
    assert create_command.is_clone
    assert create_command.use_docker
