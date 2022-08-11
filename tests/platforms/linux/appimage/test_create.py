import sys
from unittest.mock import MagicMock

import pytest

from briefcase.platforms.linux.appimage import LinuxAppImageCreateCommand


def test_create_app_creates_build_subprocess(first_app_config, tmp_path):
    """Creates, prepares, and returns a build subprocess in state."""
    command = LinuxAppImageCreateCommand(base_path=tmp_path)
    command.use_docker = True
    command.subprocess = MagicMock()
    docker = MagicMock()
    command.Docker = MagicMock()
    command.Docker.return_value = docker

    # stub out CreateCommand.create_app() calls
    command.generate_app_template = MagicMock()
    command.install_app_support_package = MagicMock()
    command.install_app_code = MagicMock()
    command.install_app_resources = MagicMock()

    command._path_index = {
        first_app_config: {"app_packages_path": "path/to/app_packages"}
    }

    state = command.create_app(first_app_config)

    # build_subprocess was returned as part of the state
    assert state.get("build_subprocess") is docker
    assert command.build_subprocess is docker

    # A docker context was created
    command.Docker.assert_called_with(command, first_app_config)

    # The docker container was prepared
    docker.prepare.assert_called_once_with()
    assert command.build_subprocess is docker

    # verify normal create_app process ran
    command.generate_app_template.assert_called_once_with(app=first_app_config)
    command.install_app_support_package.assert_called_once_with(app=first_app_config)
    command.install_app_code.assert_called_once_with(app=first_app_config)
    command.install_app_resources.assert_called_once_with(app=first_app_config)


def test_create_app_creates_build_subprocess_no_docker(first_app_config, tmp_path):
    """Creates, prepares, and returns a build subprocess in state."""
    command = LinuxAppImageCreateCommand(base_path=tmp_path)
    command.use_docker = False
    command.subprocess = MagicMock()
    docker = MagicMock()
    command.Docker = MagicMock()
    command.Docker.return_value = docker

    # stub out CreateCommand.create_app() calls
    command.generate_app_template = MagicMock()
    command.install_app_support_package = MagicMock()
    command.install_app_code = MagicMock()
    command.install_app_resources = MagicMock()

    command._path_index = {
        first_app_config: {"app_packages_path": "path/to/app_packages"}
    }

    state = command.create_app(first_app_config)

    # build_subprocess was returned as part of the state
    assert state.get("build_subprocess") is command.subprocess
    assert command.build_subprocess is command.subprocess

    # A docker context was not created, nor was it prepared
    assert command.Docker.call_count == 0
    assert docker.prepare.call_count == 0

    # The prepare call was made for subprocess
    command.subprocess.prepare.assert_called_once()

    # verify normal create_app process ran
    command.generate_app_template.assert_called_once_with(app=first_app_config)
    command.install_app_support_package.assert_called_once_with(app=first_app_config)
    command.install_app_code.assert_called_once_with(app=first_app_config)
    command.install_app_resources.assert_called_once_with(app=first_app_config)


def test_support_package_url(first_app_config, tmp_path):
    command = LinuxAppImageCreateCommand(base_path=tmp_path)

    # Set some properties of the host system for test purposes.
    command.host_arch = "wonky"
    command.platform = "tester"

    assert command.support_package_url_query == [
        ("platform", "tester"),
        ("version", f"3.{sys.version_info.minor}"),
        ("arch", "wonky"),
    ]


@pytest.mark.skipif(
    sys.platform == "win32", reason="Windows paths aren't converted in Docker context"
)
def test_install_app_dependencies(first_app_config, tmp_path):
    """If Docker is in use, a docker context is used to invoke pip."""
    first_app_config.requires = ["foo==1.2.3", "bar>=4.5"]

    command = LinuxAppImageCreateCommand(base_path=tmp_path)
    command.use_docker = True
    command.subprocess = MagicMock()
    docker = MagicMock()
    command.Docker = MagicMock()
    command.Docker.return_value = docker

    command._path_index = {
        first_app_config: {"app_packages_path": "path/to/app_packages"}
    }

    command.install_app_dependencies(first_app_config)

    # A docker context was created
    command.Docker.assert_called_with(command, first_app_config)

    # The docker container was prepared
    docker.prepare.assert_called_once_with()
    assert command.build_subprocess is docker

    # pip was invoked inside docker.
    docker.run.assert_called_with(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--upgrade",
            "--no-user",
            f"--target={tmp_path}/linux/appimage/First App/path/to/app_packages",
            "foo==1.2.3",
            "bar>=4.5",
        ],
        check=True,
    )


@pytest.mark.skipif(
    sys.platform == "win32", reason="Windows paths aren't converted in Docker context"
)
def test_install_app_dependencies_no_docker(first_app_config, tmp_path):
    """If docker is *not* in use, calls are made on raw subprocess."""
    first_app_config.requires = ["foo==1.2.3", "bar>=4.5"]

    command = LinuxAppImageCreateCommand(base_path=tmp_path)
    command.use_docker = False
    command.subprocess = MagicMock()
    docker = MagicMock()
    command.Docker = MagicMock()
    command.Docker.return_value = docker

    command._path_index = {
        first_app_config: {"app_packages_path": "path/to/app_packages"}
    }

    command.install_app_dependencies(first_app_config)

    # A docker context was not created, nor was it prepared
    assert command.Docker.call_count == 0
    assert docker.prepare.call_count == 0

    # The prepare call was made for subprocess
    command.subprocess.prepare.assert_called_once()
    assert command.build_subprocess is command.subprocess

    # pip was invoked natively
    command.subprocess.run.assert_called_with(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--upgrade",
            "--no-user",
            f"--target={tmp_path}/linux/appimage/First App/path/to/app_packages",
            "foo==1.2.3",
            "bar>=4.5",
        ],
        check=True,
    )
