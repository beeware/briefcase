import sys
from unittest.mock import MagicMock

import pytest

from briefcase.console import Console, Log
from briefcase.integrations.docker import DockerAppContext
from briefcase.integrations.subprocess import Subprocess
from briefcase.platforms.linux.appimage import LinuxAppImageCreateCommand


def test_support_package_url(tmp_path):
    command = LinuxAppImageCreateCommand(
        logger=Log(),
        console=Console(),
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )

    # Set some properties of the host system for test purposes.
    command.tools.host_arch = "wonky"

    assert (
        command.support_package_url(52)
        == f"https://briefcase-support.s3.amazonaws.com/python/3.{sys.version_info.minor}/linux/wonky/"
        f"Python-3.{sys.version_info.minor}-linux-wonky-support.b52.tar.gz"
    )


@pytest.mark.skipif(
    sys.platform == "win32", reason="Windows paths aren't converted in Docker context"
)
def test_install_app_dependencies_in_docker(first_app_config, tmp_path):
    """If Docker is in use, a docker context is used to invoke pip."""
    first_app_config.requires = ["foo==1.2.3", "bar>=4.5"]

    command = LinuxAppImageCreateCommand(
        logger=Log(),
        console=Console(),
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )
    command.use_docker = True

    # Mock the existence of Docker.
    command.tools.subprocess = MagicMock(spec_set=Subprocess)

    command._path_index = {
        first_app_config: {"app_packages_path": "path/to/app_packages"}
    }

    # Provide Docker app context
    command.tools[first_app_config].app_context = DockerAppContext(
        tools=command.tools,
        app=first_app_config,
    )
    command.tools[first_app_config].app_context.prepare(
        image_tag="briefcase/com.example.first-app:py3.X",
        dockerfile_path=tmp_path
        / "base_path"
        / "linux"
        / "appimage"
        / "First App"
        / "Dockerfile",
        app_base_path=tmp_path / "base_path",
        host_platform_path=tmp_path / "base_path" / "linux",
        host_data_path=tmp_path / "briefcase",
        python_version="3.X",
    )

    command.install_app_dependencies(first_app_config)

    # pip was invoked inside docker.
    command.tools.subprocess.run.assert_called_with(
        [
            "docker",
            "run",
            "--volume",
            f"{tmp_path / 'base_path' / 'linux'}:/app:z",
            "--volume",
            f"{tmp_path / 'briefcase'}:/home/brutus/.cache/briefcase:z",
            "--rm",
            "briefcase/com.example.first-app:py3.X",
            "python3.X",
            "-u",
            "-m",
            "pip",
            "install",
            "--upgrade",
            "--no-user",
            "--target=/app/appimage/First App/path/to/app_packages",
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

    command = LinuxAppImageCreateCommand(
        logger=Log(),
        console=Console(),
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )
    command.tools.host_os = "Linux"
    command.use_docker = False
    command.tools.subprocess = MagicMock(spec_set=Subprocess)

    command._path_index = {
        first_app_config: {"app_packages_path": "path/to/app_packages"}
    }

    command.verify_tools()
    command.verify_app_tools(first_app_config)

    command.install_app_dependencies(first_app_config)

    # Docker is not verified.
    assert not hasattr(command.tools, "docker")

    # Subprocess is used for app_context
    assert isinstance(command.tools[first_app_config].app_context, Subprocess)
    assert command.tools[first_app_config].app_context is command.tools.subprocess

    # pip was invoked natively
    command.tools[first_app_config].app_context.run.assert_called_with(
        [
            sys.executable,
            "-u",
            "-m",
            "pip",
            "install",
            "--upgrade",
            "--no-user",
            f"--target={tmp_path}/base_path/linux/appimage/First App/path/to/app_packages",
            "foo==1.2.3",
            "bar>=4.5",
        ],
        check=True,
    )
