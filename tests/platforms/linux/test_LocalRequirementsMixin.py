import shutil
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, call

import pytest

from briefcase.commands import CreateCommand
from briefcase.console import Console, Log
from briefcase.exceptions import BriefcaseCommandError
from briefcase.integrations.docker import DockerAppContext
from briefcase.integrations.subprocess import Subprocess
from briefcase.platforms.linux import LocalRequirementsMixin

from ...utils import create_file, create_tgz_file, create_zip_file


class DummyCreateCommand(LocalRequirementsMixin, CreateCommand):
    """A command that provides the stubs required to satisfy LocalRequirementsMixin."""

    platform = "Tester"
    output_format = "Dummy"

    def binary_path(self, app):
        return self.bundle_path(app) / f"{app.app_name}.bin"


@pytest.fixture
def no_docker_create_command(first_app_config, tmp_path):
    command = DummyCreateCommand(
        logger=Log(),
        console=Console(),
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )

    # Disable Docker use
    command.use_docker = False

    # Set the host architecture to something known for test purposes.
    command.tools.host_arch = "wonky"

    # Set the host system to Linux for test purposes
    command.tools.host_os = "Linux"

    # Mock the existence of Docker
    command.tools.subprocess = MagicMock(spec_set=Subprocess)

    # Mock shutil.copy to do the copy, but be observable
    command.tools.shutil.copy = MagicMock(side_effect=shutil.copy)

    command._briefcase_toml[first_app_config] = {
        "paths": {"app_packages_path": "path/to/app_packages"}
    }

    # At the time app requirements are installed, the project folder will exist.
    command.bundle_path(first_app_config).mkdir(parents=True, exist_ok=True)

    return command


@pytest.fixture
def create_command(no_docker_create_command, first_app_config, tmp_path):
    # Enable Docker use
    no_docker_create_command.use_docker = True

    # Provide Docker app context
    no_docker_create_command.tools[first_app_config].app_context = DockerAppContext(
        tools=no_docker_create_command.tools,
        app=first_app_config,
    )
    no_docker_create_command.tools[first_app_config].app_context.prepare(
        image_tag="briefcase/com.example.first-app:py3.X",
        dockerfile_path=tmp_path
        / "base_path"
        / "build"
        / "first-app"
        / "tester"
        / "dummy"
        / "Dockerfile",
        app_base_path=tmp_path / "base_path",
        host_bundle_path=tmp_path
        / "base_path"
        / "build"
        / "first-app"
        / "tester"
        / "dummy",
        host_data_path=tmp_path / "briefcase",
        python_version="3.X",
    )

    # Reset the subprocess.run mock, removing the Docker setup call
    no_docker_create_command.tools.subprocess.run.reset_mock()

    return no_docker_create_command


@pytest.fixture
def first_package(tmp_path):
    # Create a local package to be built
    create_file(
        tmp_path / "local/first/setup.py",
        content="Python config",
    )
    create_file(
        tmp_path / "local/first/first.py",
        content="Python source",
    )

    return str(tmp_path / "local/first")


@pytest.fixture
def second_package(tmp_path):
    # Create a local pre-built sdist
    create_tgz_file(
        tmp_path / "local/second-2.3.4.tar.gz",
        content=[
            ("setup.py", "Python config"),
            ("second.py", "Python source"),
        ],
    )

    return str(tmp_path / "local/second-2.3.4.tar.gz")


@pytest.fixture
def third_package(tmp_path):
    # Create a local pre-built wheel
    create_zip_file(
        tmp_path / "local/third-3.4.5-py3-none-any.whl",
        content=[
            ("MANIFEST.in", "Wheel config"),
            ("third.py", "Python source"),
        ],
    )

    return str(tmp_path / "local/third-3.4.5-py3-none-any.whl")


@pytest.fixture
def other_package(create_command, first_app_config):
    # A stale sdist, built in a previous pass
    create_tgz_file(
        create_command.local_requirements_path(first_app_config)
        / "other_package-0.1.2.tar.gz",
        content=[
            ("setup.py", "Python config"),
            ("other.py", "Python source"),
        ],
    )


@pytest.mark.skipif(
    sys.platform == "win32", reason="Windows paths aren't converted in Docker context"
)
def test_install_app_requirements_in_docker(create_command, first_app_config, tmp_path):
    """If Docker is in use, a docker context is used to invoke pip."""

    # Install requirements
    create_command.install_app_requirements(first_app_config, test_mode=False)

    # pip was invoked inside docker.
    create_command.tools.subprocess.run.assert_called_once_with(
        [
            "docker",
            "run",
            "--rm",
            "--volume",
            f"{tmp_path / 'base_path' / 'build' / 'first-app' / 'tester' / 'dummy'}:/app:z",
            "--volume",
            f"{tmp_path / 'briefcase'}:/briefcase:z",
            "briefcase/com.example.first-app:py3.X",
            "python3.X",
            "-u",
            "-X",
            "utf8",
            "-m",
            "pip",
            "install",
            "--disable-pip-version-check",
            "--no-python-version-warning",
            "--upgrade",
            "--no-user",
            "--target=/app/path/to/app_packages",
            "foo==1.2.3",
            "bar>=4.5",
        ],
        check=True,
        encoding="UTF-8",
    )

    # The local requirements path exists, but is empty
    local_requirements_path = create_command.local_requirements_path(first_app_config)
    assert local_requirements_path.exists()
    assert len(list(local_requirements_path.iterdir())) == 0


@pytest.mark.skipif(
    sys.platform == "win32", reason="Windows paths aren't converted in Docker context"
)
def test_install_app_requirements_no_docker(
    no_docker_create_command,
    first_app_config,
    tmp_path,
):
    """If docker is *not* in use, calls are made on raw subprocess."""
    # Verify the tools; this should operate in the non-docker context
    no_docker_create_command.verify_tools()
    no_docker_create_command.verify_app_tools(first_app_config)

    # Install requirements
    no_docker_create_command.install_app_requirements(first_app_config, test_mode=False)

    # Docker is not verified.
    assert not hasattr(no_docker_create_command.tools, "docker")

    # Subprocess is used for app_context
    assert isinstance(
        no_docker_create_command.tools[first_app_config].app_context, Subprocess
    )
    assert (
        no_docker_create_command.tools[first_app_config].app_context
        is no_docker_create_command.tools.subprocess
    )

    # pip was invoked natively
    no_docker_create_command.tools[
        first_app_config
    ].app_context.run.assert_called_once_with(
        [
            sys.executable,
            "-u",
            "-X",
            "utf8",
            "-m",
            "pip",
            "install",
            "--disable-pip-version-check",
            "--no-python-version-warning",
            "--upgrade",
            "--no-user",
            f"--target={tmp_path}/base_path/build/first-app/tester/dummy/path/to/app_packages",
            "foo==1.2.3",
            "bar>=4.5",
        ],
        check=True,
        encoding="UTF-8",
    )

    # The local requirements path exists, but is empty
    local_requirements_path = no_docker_create_command.local_requirements_path(
        first_app_config
    )
    assert local_requirements_path.exists()
    assert len(list(local_requirements_path.iterdir())) == 0


@pytest.mark.skipif(
    sys.platform == "win32", reason="Windows paths aren't converted in Docker context"
)
def test_install_app_requirements_with_locals(
    create_command,
    first_app_config,
    tmp_path,
    first_package,  # A local folder to be built
    second_package,  # A pre-built sdist
    third_package,  # A pre-built wheel
    other_package,  # A stale local requirement
):
    """If the app has local requirements, they are compiled into sdists for
    installation."""
    # Add local requirements
    first_app_config.requires.extend([first_package, second_package, third_package])

    # Mock the side effect of building an sdist
    def build_sdist(*args, **kwargs):
        # Extract the folder name; assume that's the name of the package
        name = Path(args[0][-1]).name
        create_tgz_file(
            create_command.local_requirements_path(first_app_config)
            / f"{name}-1.2.3.tar.gz",
            content=[
                ("setup.py", "Python config"),
                ("local.py", "Python source"),
            ],
        )

    create_command.tools.subprocess.check_output.side_effect = build_sdist

    # Install requirements
    create_command.install_app_requirements(first_app_config, test_mode=False)

    # An sdist was built for the local package
    create_command.tools.subprocess.check_output.assert_called_once_with(
        [
            sys.executable,
            "-X",
            "utf8",
            "-m",
            "build",
            "--sdist",
            "--outdir",
            tmp_path
            / "base_path"
            / "build"
            / "first-app"
            / "tester"
            / "dummy"
            / "_requirements",
            str(tmp_path / "local/first"),
        ],
        encoding="UTF-8",
    )

    # An attempt was made to copy the prebuilt packages
    create_command.tools.shutil.copy.mock_calls = [
        call(
            str(tmp_path / "local/second-2.3.4.tar.gz"),
            tmp_path
            / "base_path"
            / "build"
            / "first-app"
            / "tester"
            / "dummy"
            / "_requirements",
        ),
        call(
            str(tmp_path / "local/third-3.4.5-py3-none-any.whl"),
            tmp_path
            / "base_path"
            / "build"
            / "first-app"
            / "tester"
            / "dummy"
            / "_requirements",
        ),
    ]

    # pip was invoked inside docker.
    create_command.tools.subprocess.run.assert_called_once_with(
        [
            "docker",
            "run",
            "--rm",
            "--volume",
            f"{tmp_path / 'base_path' / 'build' / 'first-app' / 'tester' / 'dummy'}:/app:z",
            "--volume",
            f"{tmp_path / 'briefcase'}:/briefcase:z",
            "briefcase/com.example.first-app:py3.X",
            "python3.X",
            "-u",
            "-X",
            "utf8",
            "-m",
            "pip",
            "install",
            "--disable-pip-version-check",
            "--no-python-version-warning",
            "--upgrade",
            "--no-user",
            "--target=/app/path/to/app_packages",
            "foo==1.2.3",
            "bar>=4.5",
            "/app/_requirements/first-1.2.3.tar.gz",
            "/app/_requirements/second-2.3.4.tar.gz",
            "/app/_requirements/third-3.4.5-py3-none-any.whl",
        ],
        check=True,
        encoding="UTF-8",
    )

    # The local requirements path exists, and contains the compiled sdist, the
    # pre-existing sdist, and the pre-existing wheel; the old requirement has
    # been purged.
    local_requirements_path = create_command.local_requirements_path(first_app_config)
    assert local_requirements_path.exists()
    assert [f.name for f in sorted(local_requirements_path.iterdir())] == [
        "first-1.2.3.tar.gz",
        "second-2.3.4.tar.gz",
        "third-3.4.5-py3-none-any.whl",
    ]


@pytest.mark.skipif(
    sys.platform == "win32", reason="Windows paths aren't converted in Docker context"
)
def test_install_app_requirements_with_bad_local(
    create_command,
    first_app_config,
    tmp_path,
    first_package,  # A local folder to be built
    other_package,  # A stale local requirement
):
    """If the app has local requirement that can't be built, an error is raised."""
    # Add a local requirement
    first_app_config.requires.append(first_package)

    # Mock the building an sdist raising an error
    create_command.tools.subprocess.check_output.side_effect = (
        subprocess.CalledProcessError(
            cmd=["python", "-m", "build", "..."], returncode=1
        )
    )

    # Install requirements
    with pytest.raises(
        BriefcaseCommandError,
        match=r"Unable to build sdist for .*/local/first",
    ):
        create_command.install_app_requirements(first_app_config, test_mode=False)

    # An attempt to build the sdist was made
    create_command.tools.subprocess.check_output.assert_called_once_with(
        [
            sys.executable,
            "-X",
            "utf8",
            "-m",
            "build",
            "--sdist",
            "--outdir",
            tmp_path
            / "base_path"
            / "build"
            / "first-app"
            / "tester"
            / "dummy"
            / "_requirements",
            str(tmp_path / "local/first"),
        ],
        encoding="UTF-8",
    )

    # pip was *not* invoked inside docker.
    create_command.tools.subprocess.run.assert_not_called()

    # The local requirements path exists, and is empty. It has been purged, but not refilled.
    local_requirements_path = create_command.local_requirements_path(first_app_config)
    assert local_requirements_path.exists()
    assert len(list(local_requirements_path.iterdir())) == 0


@pytest.mark.skipif(
    sys.platform == "win32", reason="Windows paths aren't converted in Docker context"
)
def test_install_app_requirements_with_missing_local_build(
    create_command,
    first_app_config,
    tmp_path,
):
    """If the app references a requirement that needs to be built, but is missing, an
    error is raised."""
    # Define a local requirement, but don't create the files it points at
    first_app_config.requires.append(str(tmp_path / "local/first"))

    # Install requirements
    with pytest.raises(
        BriefcaseCommandError,
        match=r"Unable to find local requirement .*/local/first",
    ):
        create_command.install_app_requirements(first_app_config, test_mode=False)

    # No attempt to build the sdist was made
    create_command.tools.subprocess.check_output.assert_not_called()

    # pip was *not* invoked inside docker.
    create_command.tools.subprocess.run.assert_not_called()

    # The local requirements path exists, and is empty. It has been purged, but not refilled.
    local_requirements_path = create_command.local_requirements_path(first_app_config)
    assert local_requirements_path.exists()
    assert len(list(local_requirements_path.iterdir())) == 0


@pytest.mark.skipif(
    sys.platform == "win32", reason="Windows paths aren't converted in Docker context"
)
def test_install_app_requirements_with_bad_local_file(
    create_command,
    first_app_config,
    tmp_path,
):
    """If the app references a local requirement file that doesn't exist, an error is
    raised."""
    # Add a local requirement that doesn't exist
    first_app_config.requires.append(str(tmp_path / "local/missing-2.3.4.tar.gz"))

    # Install requirements
    with pytest.raises(
        BriefcaseCommandError,
        match=r"Unable to find local requirement .*/local/missing-2.3.4.tar.gz",
    ):
        create_command.install_app_requirements(first_app_config, test_mode=False)

    # An attempt was made to copy the package
    create_command.tools.shutil.copy.assert_called_once_with(
        str(tmp_path / "local/missing-2.3.4.tar.gz"),
        tmp_path
        / "base_path"
        / "build"
        / "first-app"
        / "tester"
        / "dummy"
        / "_requirements",
    )

    # No attempt was made to build the sdist
    create_command.tools.subprocess.check_output.assert_not_called()

    # pip was *not* invoked inside docker.
    create_command.tools.subprocess.run.assert_not_called()

    # The local requirements path exists, and is empty. It has been purged, but not refilled.
    local_requirements_path = create_command.local_requirements_path(first_app_config)
    assert local_requirements_path.exists()
    assert len(list(local_requirements_path.iterdir())) == 0
