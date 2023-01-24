import shutil
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, call

import pytest

from briefcase.commands.base import BriefcaseCommandError
from briefcase.console import Console, Log
from briefcase.integrations.docker import DockerAppContext
from briefcase.integrations.subprocess import Subprocess
from briefcase.platforms.linux.appimage import LinuxAppImageCreateCommand

from ....utils import create_file, create_tgz_file, create_zip_file


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
def test_install_app_requirements_in_docker(first_app_config, tmp_path):
    """If Docker is in use, a docker context is used to invoke pip."""

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

    # At the time app requirements are installed, the project folder will exist.
    #
    command.project_path(first_app_config).mkdir(parents=True, exist_ok=True)

    # Reset the subprocess.run mock, removing the Docker setup call
    command.tools.subprocess.run.reset_mock()

    # Install requirements
    command.install_app_requirements(first_app_config, test_mode=False)

    # pip was invoked inside docker.
    command.tools.subprocess.run.assert_called_once_with(
        [
            "docker",
            "run",
            "--rm",
            "--volume",
            f"{tmp_path / 'base_path' / 'linux'}:/app:z",
            "--volume",
            f"{tmp_path / 'briefcase'}:/home/brutus/.cache/briefcase:z",
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

    # The local requirements path exists, but is empty
    assert command.local_requirements_path(first_app_config).exists()
    assert len(list(command.local_requirements_path(first_app_config).iterdir())) == 0


@pytest.mark.skipif(
    sys.platform == "win32", reason="Windows paths aren't converted in Docker context"
)
def test_install_app_requirements_no_docker(first_app_config, tmp_path):
    """If docker is *not* in use, calls are made on raw subprocess."""

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

    # At the time app requirements are installed, the project folder will exist.
    #
    command.project_path(first_app_config).mkdir(parents=True, exist_ok=True)

    # Install requirements
    command.install_app_requirements(first_app_config, test_mode=False)

    # Docker is not verified.
    assert not hasattr(command.tools, "docker")

    # Subprocess is used for app_context
    assert isinstance(command.tools[first_app_config].app_context, Subprocess)
    assert command.tools[first_app_config].app_context is command.tools.subprocess

    # pip was invoked natively
    command.tools[first_app_config].app_context.run.assert_called_once_with(
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

    # The local requirements path exists, but is empty
    assert command.local_requirements_path(first_app_config).exists()
    assert len(list(command.local_requirements_path(first_app_config).iterdir())) == 0


@pytest.mark.skipif(
    sys.platform == "win32", reason="Windows paths aren't converted in Docker context"
)
def test_install_app_requirements_with_locals(first_app_config, tmp_path):
    """If the app has local requirements, they are compiled into sdists for
    installation."""
    # Add a local requirements that are:
    # 1. a folder
    first_app_config.requires.append(str(tmp_path / "local" / "first"))
    # 2. an sdist tarball
    first_app_config.requires.append(str(tmp_path / "local" / "second-2.3.4.tar.gz"))
    # 3. A wheel
    first_app_config.requires.append(
        str(tmp_path / "local" / "third-3.4.5-py3-none-any.whl")
    )

    command = LinuxAppImageCreateCommand(
        logger=Log(),
        console=Console(),
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )
    command.use_docker = True

    # Mock the existence of Docker and shutil.copy
    command.tools.subprocess = MagicMock(spec_set=Subprocess)
    command.tools.shutil.copy = MagicMock(side_effect=shutil.copy)

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

    # Mock the side effect of building an sdist
    def build_sdist(*args, **kwargs):
        # Extract the folder name; assume that's the name of the package
        name = Path(args[0][-1]).name
        create_tgz_file(
            command.local_requirements_path(first_app_config) / f"{name}-1.2.3.tar.gz",
            content=[
                ("setup.py", "Python config"),
                ("local.py", "Python source"),
            ],
        )

    command.tools.subprocess.check_output.side_effect = build_sdist

    # Mock the existence of a stale sdist
    create_tgz_file(
        command.local_requirements_path(first_app_config)
        / "other_package-0.1.2.tar.gz",
        content=[
            ("setup.py", "Python config"),
            ("other.py", "Python source"),
        ],
    )

    # Create the local project folder
    create_file(
        tmp_path / "local" / "first" / "setup.py",
        content="Python config",
    )
    create_file(
        tmp_path / "local" / "first" / "first.py",
        content="Python source",
    )

    # Create a local pre-built sdist
    create_tgz_file(
        tmp_path / "local" / "second-2.3.4.tar.gz",
        content=[
            ("setup.py", "Python config"),
            ("second.py", "Python source"),
        ],
    )

    # Create a local wheel
    create_zip_file(
        tmp_path / "local" / "third-3.4.5-py3-none-any.whl",
        content=[
            ("MANIFEST.in", "Wheel config"),
            ("third.py", "Python source"),
        ],
    )

    # Reset the subprocess.run mock, removing the Docker setup call
    command.tools.subprocess.run.reset_mock()

    # Install requirements
    command.install_app_requirements(first_app_config, test_mode=False)

    # An sdist was built for the local package
    command.tools.subprocess.check_output.assert_called_once_with(
        [
            sys.executable,
            "-m",
            "build",
            "--sdist",
            "--outdir",
            tmp_path
            / "base_path"
            / "linux"
            / "appimage"
            / "First App"
            / "_requirements",
            str(tmp_path / "local" / "first"),
        ]
    )

    # An attempt was made to copy the prebuilt packages
    command.tools.shutil.copy.mock_calls = [
        call(
            str(tmp_path / "local" / "second-2.3.4.tar.gz"),
            tmp_path
            / "base_path"
            / "linux"
            / "appimage"
            / "First App"
            / "_requirements",
        ),
        call(
            str(tmp_path / "local" / "third-3.4.5-py3-none-any.whl"),
            tmp_path
            / "base_path"
            / "linux"
            / "appimage"
            / "First App"
            / "_requirements",
        ),
    ]

    # pip was invoked inside docker.
    command.tools.subprocess.run.assert_called_once_with(
        [
            "docker",
            "run",
            "--rm",
            "--volume",
            f"{tmp_path / 'base_path' / 'linux'}:/app:z",
            "--volume",
            f"{tmp_path / 'briefcase'}:/home/brutus/.cache/briefcase:z",
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
            "/app/appimage/First App/_requirements/first-1.2.3.tar.gz",
            "/app/appimage/First App/_requirements/second-2.3.4.tar.gz",
            "/app/appimage/First App/_requirements/third-3.4.5-py3-none-any.whl",
        ],
        check=True,
    )

    # The local requirements path exists, and contains the compiled sdist, the
    # pre-existing sdist, and the pre-existing wheel; the old requirement has
    # been purged.
    assert command.local_requirements_path(first_app_config).exists()
    assert [
        f.name
        for f in sorted(command.local_requirements_path(first_app_config).iterdir())
    ] == [
        "first-1.2.3.tar.gz",
        "second-2.3.4.tar.gz",
        "third-3.4.5-py3-none-any.whl",
    ]


@pytest.mark.skipif(
    sys.platform == "win32", reason="Windows paths aren't converted in Docker context"
)
def test_install_app_requirements_with_bad_local(first_app_config, tmp_path):
    """If the app has local requirement that can't be built, an error is
    raised."""
    # Add a local requirement
    first_app_config.requires.append(str(tmp_path / "local" / "first"))

    command = LinuxAppImageCreateCommand(
        logger=Log(),
        console=Console(),
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )
    command.use_docker = True

    # Mock the existence of Docker and shutil.copy
    command.tools.subprocess = MagicMock(spec_set=Subprocess)
    command.tools.shutil.copy = MagicMock(side_effect=shutil.copy)

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

    # Mock the building an sdist raising an error
    command.tools.subprocess.check_output.side_effect = subprocess.CalledProcessError(
        cmd=["python", "-m", "build", "..."], returncode=1
    )

    # Mock the existence of a stale sdist
    create_tgz_file(
        command.local_requirements_path(first_app_config)
        / "other_package-0.1.2.tar.gz",
        content=[
            ("setup.py", "Python config"),
            ("other.py", "Python source"),
        ],
    )

    # Create the local project folder
    create_file(
        tmp_path / "local" / "first" / "setup.py",
        content="Python config",
    )
    create_file(
        tmp_path / "local" / "first" / "first.py",
        content="Python source",
    )

    # Reset the subprocess.run mock, removing the Docker setup call
    command.tools.subprocess.run.reset_mock()

    # Install requirements
    with pytest.raises(
        BriefcaseCommandError,
        match=r"Unable to build sdist for .*/local/first",
    ):
        command.install_app_requirements(first_app_config, test_mode=False)

    # An attempt to build the sdist was made
    command.tools.subprocess.check_output.assert_called_once_with(
        [
            sys.executable,
            "-m",
            "build",
            "--sdist",
            "--outdir",
            tmp_path
            / "base_path"
            / "linux"
            / "appimage"
            / "First App"
            / "_requirements",
            str(tmp_path / "local" / "first"),
        ]
    )

    # pip was *not* invoked inside docker.
    command.tools.subprocess.run.assert_not_called()

    # The local requirements path exists, and is empty. It has been purged, but not refilled.
    assert command.local_requirements_path(first_app_config).exists()
    assert len(list(command.local_requirements_path(first_app_config).iterdir())) == 0


@pytest.mark.skipif(
    sys.platform == "win32", reason="Windows paths aren't converted in Docker context"
)
def test_install_app_requirements_with_missing_local_build(first_app_config, tmp_path):
    """If the app references a requirement that needs to be built, but is
    missing, an error is raised."""
    # Add a local requirement, but don't create the requirement
    first_app_config.requires.append(str(tmp_path / "local" / "first"))

    command = LinuxAppImageCreateCommand(
        logger=Log(),
        console=Console(),
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )
    command.use_docker = True

    # Mock the existence of Docker and shutil.copy
    command.tools.subprocess = MagicMock(spec_set=Subprocess)
    command.tools.shutil.copy = MagicMock(side_effect=shutil.copy)

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

    # Mock the building an sdist raising an error
    command.tools.subprocess.check_output.side_effect = subprocess.CalledProcessError(
        cmd=["python", "-m", "build", "..."], returncode=1
    )

    # Mock the existence of a stale sdist
    create_tgz_file(
        command.local_requirements_path(first_app_config)
        / "other_package-0.1.2.tar.gz",
        content=[
            ("setup.py", "Python config"),
            ("other.py", "Python source"),
        ],
    )

    # Don't create the local project folder

    # Reset the subprocess.run mock, removing the Docker setup call
    command.tools.subprocess.run.reset_mock()

    # Install requirements
    with pytest.raises(
        BriefcaseCommandError,
        match=r"Unable to find local requirement .*/local/first",
    ):
        command.install_app_requirements(first_app_config, test_mode=False)

    # No attempt to build the sdist was made
    command.tools.subprocess.check_output.assert_not_called()

    # pip was *not* invoked inside docker.
    command.tools.subprocess.run.assert_not_called()

    # The local requirements path exists, and is empty. It has been purged, but not refilled.
    assert command.local_requirements_path(first_app_config).exists()
    assert len(list(command.local_requirements_path(first_app_config).iterdir())) == 0


@pytest.mark.skipif(
    sys.platform == "win32", reason="Windows paths aren't converted in Docker context"
)
def test_install_app_requirements_with_bad_local_file(first_app_config, tmp_path):
    """If the app references a local requirement file that doesn't exist, an
    error is raised."""
    # Add a local requirement that doesn't exist
    first_app_config.requires.append(str(tmp_path / "local" / "other-2.3.4.tar.gz"))

    command = LinuxAppImageCreateCommand(
        logger=Log(),
        console=Console(),
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )
    command.use_docker = True

    # Mock the existence of Docker and shutil.copy
    command.tools.subprocess = MagicMock(spec_set=Subprocess)
    command.tools.shutil.copy = MagicMock(side_effect=shutil.copy)

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

    # Mock the building an sdist raising an error
    command.tools.subprocess.check_output.side_effect = subprocess.CalledProcessError(
        cmd=["python", "-m", "build", "..."], returncode=1
    )

    # Mock the existence of a stale sdist
    create_tgz_file(
        command.local_requirements_path(first_app_config)
        / "other_package-0.1.2.tar.gz",
        content=[
            ("setup.py", "Python config"),
            ("other.py", "Python source"),
        ],
    )

    # Don't create the local requirement file

    # Reset the subprocess.run mock, removing the Docker setup call
    command.tools.subprocess.run.reset_mock()

    # Install requirements
    with pytest.raises(
        BriefcaseCommandError,
        match=r"Unable to find local requirement .*/local/other-2.3.4.tar.gz",
    ):
        command.install_app_requirements(first_app_config, test_mode=False)

    # An attempt was made to copy the package
    command.tools.shutil.copy.assert_called_once_with(
        str(tmp_path / "local" / "other-2.3.4.tar.gz"),
        tmp_path / "base_path" / "linux" / "appimage" / "First App" / "_requirements",
    )

    # No attempt was made to build the sdist
    command.tools.subprocess.check_output.assert_not_called()

    # pip was *not* invoked inside docker.
    command.tools.subprocess.run.assert_not_called()

    # The local requirements path exists, and is empty. It has been purged, but not refilled.
    assert command.local_requirements_path(first_app_config).exists()
    assert len(list(command.local_requirements_path(first_app_config).iterdir())) == 0
