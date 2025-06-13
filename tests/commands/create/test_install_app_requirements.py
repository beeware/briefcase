import datetime
import os
import subprocess
import sys
from unittest import mock

import pytest
import tomli_w

import briefcase
from briefcase.commands.create import _is_local_path
from briefcase.console import LogLevel
from briefcase.exceptions import BriefcaseCommandError, RequirementsInstallError
from briefcase.integrations.subprocess import Subprocess

GENERATED_DATETIME = "# Generated 2024-05-02 12:00:00.000500"


@pytest.fixture
def create_command(create_command, myapp):
    # mock subprocess app context for this app
    create_command.tools[myapp].app_context = mock.MagicMock(spec_set=Subprocess)
    return create_command


@pytest.fixture
def mock_now(monkeypatch):
    """Monkeypatch the ``datetime.now`` inside ``briefcase.commands.create``.

    When this fixture is used, the datetime is locked to 2024 May 2 @ 12:00:00:000500.
    """
    now = datetime.datetime(2024, 5, 2, 12, 0, 0, 500)
    datetime_mock = mock.MagicMock(wraps=datetime.datetime)
    datetime_mock.now.return_value = now
    monkeypatch.setattr(briefcase.commands.create, "datetime", datetime_mock)
    return now


def create_installation_artefacts(app_packages_path, packages):
    """Utility method for generating a function that will mock installation artefacts.

    Creates a function that when invoked, creates a dummy ``__init__.py``
    and ``__main__.py`` for each package named in ``packages``.

    :param app_packages_path: The pathlib object where app packages will be installed
    :param packages: A list of package names to mock.
    :returns: A function that will create files to mock the named installed packages.
    """

    def _create_installation_artefacts(*args, **kwargs):
        for package in packages:
            package_path = app_packages_path / package
            package_path.mkdir(parents=True)
            with (package_path / "__init__.py").open("w", encoding="utf-8") as f:
                f.write("")
            with (package_path / "__main__.py").open("w", encoding="utf-8") as f:
                f.write('print("I am {package}")')

    return _create_installation_artefacts


def test_bad_path_index(create_command, myapp, bundle_path, app_requirements_path):
    """If the app's path index doesn't declare a destination for requirements, an error
    is raised."""
    # Write a briefcase.toml that is missing app_packages_path and app_requirements_path
    with (bundle_path / "briefcase.toml").open("wb") as f:
        index = {
            "paths": {
                "app_path": "path/to/app",
                "support_path": "path/to/support",
            }
        }
        tomli_w.dump(index, f)

    # Set up requirements for the app
    myapp.requires = ["first", "second", "third"]

    # Install requirements
    with pytest.raises(
        BriefcaseCommandError,
        match=r"Application path index file does not define `app_requirements_path` or `app_packages_path`",
    ):
        create_command.install_app_requirements(myapp)

    # pip wasn't invoked
    create_command.tools[myapp].app_context.run.assert_not_called()

    # requirements.txt doesn't exist either
    assert not app_requirements_path.exists()

    # Original app definitions haven't changed
    assert myapp.requires == ["first", "second", "third"]
    assert myapp.test_requires is None


def test_app_packages_no_requires(
    create_command,
    myapp,
    app_packages_path,
    app_packages_path_index,
):
    """If an app has no requirements, install_app_requirements is a no-op."""
    myapp.requires = None

    create_command.install_app_requirements(myapp)

    # No request was made to install requirements
    create_command.tools[myapp].app_context.run.assert_not_called()


def test_app_packages_empty_requires(
    create_command,
    myapp,
    app_packages_path,
    app_packages_path_index,
):
    """If an app has an empty requirements list, install_app_requirements is a no-op."""
    myapp.requires = []

    create_command.install_app_requirements(myapp)

    # No request was made to install requirements
    create_command.tools[myapp].app_context.run.assert_not_called()


def test_app_packages_valid_requires(
    create_command,
    myapp,
    app_packages_path,
    app_packages_path_index,
):
    """If an app has a valid list of requirements, pip is invoked."""
    myapp.requires = ["first", "second==1.2.3", "third>=3.2.1"]

    create_command.install_app_requirements(myapp)

    # A request was made to install requirements
    create_command.tools[myapp].app_context.run.assert_called_with(
        [
            sys.executable,
            "-u",
            "-X",
            "utf8",
            "-m",
            "pip",
            "install",
            "--disable-pip-version-check",
            "--upgrade",
            "--no-user",
            f"--target={app_packages_path}",
            "first",
            "second==1.2.3",
            "third>=3.2.1",
        ],
        check=True,
        encoding="UTF-8",
    )

    # Original app definitions haven't changed
    assert myapp.requires == ["first", "second==1.2.3", "third>=3.2.1"]
    assert myapp.test_requires is None


def test_app_packages_requirement_installer_args_no_paths(
    create_command,
    myapp,
    app_packages_path,
    app_path,
    app_packages_path_index,
):
    """If an app has requirement installer arguments, they are used in pip install."""
    (create_command.base_path / "packages").mkdir(exist_ok=True)
    myapp.requirement_installer_args = ["--no-cache"]
    myapp.requires = ["package"]

    create_command.install_app_requirements(myapp)

    # A request was made to install requirements
    create_command.tools[myapp].app_context.run.assert_called_with(
        [
            sys.executable,
            "-u",
            "-X",
            "utf8",
            "-m",
            "pip",
            "install",
            "--disable-pip-version-check",
            "--upgrade",
            "--no-user",
            f"--target={app_packages_path}",
            "--no-cache",
            "package",
        ],
        check=True,
        encoding="UTF-8",
    )


def test_app_packages_requirement_installer_args_path_transformed(
    create_command,
    myapp,
    app_packages_path,
    app_path,
    app_packages_path_index,
):
    """If an app's requirement installer arguments includes a relative path that exists,
    it is transformed to an absolute path."""
    (create_command.base_path / "packages").mkdir(exist_ok=True)
    myapp.requirement_installer_args = ["--extra-index-url", "./packages"]
    myapp.requires = ["package"]

    create_command.install_app_requirements(myapp)

    # A request was made to install requirements
    create_command.tools[myapp].app_context.run.assert_called_with(
        [
            sys.executable,
            "-u",
            "-X",
            "utf8",
            "-m",
            "pip",
            "install",
            "--disable-pip-version-check",
            "--upgrade",
            "--no-user",
            f"--target={app_packages_path}",
            "--extra-index-url",
            os.path.abspath(create_command.base_path / "packages"),
            "package",
        ],
        check=True,
        encoding="UTF-8",
    )


def test_app_packages_requirement_installer_args_coincidental_path_not_transformed(
    create_command,
    myapp,
    app_packages_path,
    app_path,
    app_packages_path_index,
):
    """If an app's requirement installer arguments includes a path that exists,
    but it starts with `-`, it is used as-is."""
    (create_command.base_path / "-f" / "wheels").mkdir(parents=True, exist_ok=True)
    myapp.requirement_installer_args = ["-f./wheels"]
    myapp.requires = ["package"]

    create_command.install_app_requirements(myapp)

    # A request was made to install requirements
    create_command.tools[myapp].app_context.run.assert_called_with(
        [
            sys.executable,
            "-u",
            "-X",
            "utf8",
            "-m",
            "pip",
            "install",
            "--disable-pip-version-check",
            "--upgrade",
            "--no-user",
            f"--target={app_packages_path}",
            "-f./wheels",
            "package",
        ],
        check=True,
        encoding="UTF-8",
    )


def test_app_packages_requirement_installer_args_path_not_transformed(
    create_command,
    myapp,
    app_packages_path,
    app_path,
    app_packages_path_index,
):
    """If an app's requirement installer arguments have an argument that looks like a local path,
    but does not resolve to an existing path, it is used as-is."""
    (create_command.base_path / "packages").unlink(missing_ok=True)
    myapp.requirement_installer_args = ["--extra-index-url", "./packages"]
    myapp.requires = ["package"]

    create_command.install_app_requirements(myapp)

    # A request was made to install requirements
    create_command.tools[myapp].app_context.run.assert_called_with(
        [
            sys.executable,
            "-u",
            "-X",
            "utf8",
            "-m",
            "pip",
            "install",
            "--disable-pip-version-check",
            "--upgrade",
            "--no-user",
            f"--target={app_packages_path}",
            "--extra-index-url",
            "./packages",
            "package",
        ],
        check=True,
        encoding="UTF-8",
    )


def test_app_packages_requirement_installer_args_combined_argument_not_transformed(
    create_command,
    myapp,
    app_packages_path,
    app_path,
    app_packages_path_index,
):
    """If an app's requirement installer arguments use a combined argument,
    paths are not modified."""
    (create_command.base_path / "packages").mkdir(exist_ok=True)
    myapp.requirement_installer_args = ["--extra-index-url=./packages"]
    myapp.requires = ["package"]

    create_command.install_app_requirements(myapp)

    # A request was made to install requirements
    create_command.tools[myapp].app_context.run.assert_called_with(
        [
            sys.executable,
            "-u",
            "-X",
            "utf8",
            "-m",
            "pip",
            "install",
            "--disable-pip-version-check",
            "--upgrade",
            "--no-user",
            f"--target={app_packages_path}",
            "--extra-index-url=./packages",
            "package",
        ],
        check=True,
        encoding="UTF-8",
    )


def test_app_packages_valid_requires_no_support_package(
    create_command,
    myapp,
    app_packages_path,
    app_packages_path_index,
):
    """If the template doesn't specify a support package, the cross-platform site isn't
    specified."""
    myapp.requires = ["first", "second==1.2.3", "third>=3.2.1"]

    # Override the cache of paths to specify an app packages path, but no support package path
    create_command._briefcase_toml[myapp] = {
        "paths": {"app_packages_path": "path/to/app_packages"}
    }

    create_command.install_app_requirements(myapp)

    # A request was made to install requirements
    create_command.tools[myapp].app_context.run.assert_called_with(
        [
            sys.executable,
            "-u",
            "-X",
            "utf8",
            "-m",
            "pip",
            "install",
            "--disable-pip-version-check",
            "--upgrade",
            "--no-user",
            f"--target={app_packages_path}",
            "first",
            "second==1.2.3",
            "third>=3.2.1",
        ],
        check=True,
        encoding="UTF-8",
    )

    # Original app definitions haven't changed
    assert myapp.requires == ["first", "second==1.2.3", "third>=3.2.1"]
    assert myapp.test_requires is None


def test_app_packages_invalid_requires(
    create_command,
    myapp,
    app_packages_path,
    app_packages_path_index,
):
    """If an app has a valid list of requirements, pip is invoked."""
    myapp.requires = ["does-not-exist"]

    # Unfortunately, no way to tell the difference between "offline" and
    # "your requirements are invalid"; pip returns status code 1 for all
    # failures.
    create_command.tools[
        myapp
    ].app_context.run.side_effect = subprocess.CalledProcessError(
        cmd=["python", "-u", "-m", "pip", "..."], returncode=1
    )

    with pytest.raises(RequirementsInstallError):
        create_command.install_app_requirements(myapp)

    # But the request to install was still made
    create_command.tools[myapp].app_context.run.assert_called_with(
        [
            sys.executable,
            "-u",
            "-X",
            "utf8",
            "-m",
            "pip",
            "install",
            "--disable-pip-version-check",
            "--upgrade",
            "--no-user",
            f"--target={app_packages_path}",
            "does-not-exist",
        ],
        check=True,
        encoding="UTF-8",
    )

    # Original app definitions haven't changed
    assert myapp.requires == ["does-not-exist"]
    assert myapp.test_requires is None


def test_app_packages_offline(
    create_command,
    myapp,
    app_packages_path,
    app_packages_path_index,
):
    """If user is offline, pip fails."""
    myapp.requires = ["first", "second", "third"]

    # Unfortunately, no way to tell the difference between "offline" and
    # "your requirements are invalid"; pip returns status code 1 for all
    # failures.
    create_command.tools[
        myapp
    ].app_context.run.side_effect = subprocess.CalledProcessError(
        cmd=["python", "-u", "-m", "pip", "..."], returncode=1
    )

    with pytest.raises(RequirementsInstallError):
        create_command.install_app_requirements(myapp)

    # But the request to install was still made
    create_command.tools[myapp].app_context.run.assert_called_with(
        [
            sys.executable,
            "-u",
            "-X",
            "utf8",
            "-m",
            "pip",
            "install",
            "--disable-pip-version-check",
            "--upgrade",
            "--no-user",
            f"--target={app_packages_path}",
            "first",
            "second",
            "third",
        ],
        check=True,
        encoding="UTF-8",
    )

    # Original app definitions haven't changed
    assert myapp.requires == ["first", "second", "third"]
    assert myapp.test_requires is None


@pytest.mark.parametrize("logging_level", [LogLevel.INFO, LogLevel.DEEP_DEBUG])
def test_app_packages_install_requirements(
    create_command,
    myapp,
    app_packages_path,
    app_packages_path_index,
    logging_level,
):
    """Requirements can be installed."""
    # Configure logging level
    create_command.console.verbosity = logging_level

    # Set up the app requirements
    myapp.requires = ["first", "second", "third"]

    # The side effect of calling pip is creating installation artefacts
    create_command.tools[
        myapp
    ].app_context.run.side_effect = create_installation_artefacts(
        app_packages_path, myapp.requires
    )

    # Install the requirements
    create_command.install_app_requirements(myapp)

    # The request to install was made
    create_command.tools[myapp].app_context.run.assert_called_with(
        [
            sys.executable,
            "-u",
            "-X",
            "utf8",
            "-m",
            "pip",
            "install",
            "--disable-pip-version-check",
            "--upgrade",
            "--no-user",
            f"--target={app_packages_path}",
        ]
        + (["-vv"] if logging_level == LogLevel.DEEP_DEBUG else [])
        + ["first", "second", "third"],
        check=True,
        encoding="UTF-8",
    )

    # The new app packages have installation artefacts created
    assert (app_packages_path / "first").exists()
    assert (app_packages_path / "first/__main__.py").exists()
    assert (app_packages_path / "second").exists()
    assert (app_packages_path / "second/__main__.py").exists()
    assert (app_packages_path / "third").exists()
    assert (app_packages_path / "third/__main__.py").exists()

    # Original app definitions haven't changed
    assert myapp.requires == ["first", "second", "third"]
    assert myapp.test_requires is None


def test_app_packages_replace_existing_requirements(
    create_command,
    myapp,
    app_packages_path,
    app_packages_path_index,
):
    """If the app has already had requirements installed, they are removed first."""
    # Create some existing requirements
    create_installation_artefacts(app_packages_path, ["old", "ancient"])()

    # Set up the app requirements
    myapp.requires = ["first", "second", "third"]

    # The side effect of calling pip is creating installation artefacts
    create_command.tools[
        myapp
    ].app_context.run.side_effect = create_installation_artefacts(
        app_packages_path, myapp.requires
    )

    # Install the requirements
    create_command.install_app_requirements(myapp)

    # The request to install was still made
    create_command.tools[myapp].app_context.run.assert_called_with(
        [
            sys.executable,
            "-u",
            "-X",
            "utf8",
            "-m",
            "pip",
            "install",
            "--disable-pip-version-check",
            "--upgrade",
            "--no-user",
            f"--target={app_packages_path}",
            "first",
            "second",
            "third",
        ],
        check=True,
        encoding="UTF-8",
    )

    # The new app packages have installation artefacts created
    assert (app_packages_path / "first").exists()
    assert (app_packages_path / "first/__main__.py").exists()
    assert (app_packages_path / "second").exists()
    assert (app_packages_path / "second/__main__.py").exists()
    assert (app_packages_path / "third").exists()
    assert (app_packages_path / "third/__main__.py").exists()

    # The old app packages no longer exist.
    assert not (app_packages_path / "old").exists()
    assert not (app_packages_path / "ancient").exists()

    # Original app definitions haven't changed
    assert myapp.requires == ["first", "second", "third"]
    assert myapp.test_requires is None


def test_app_requirements_no_requires(
    create_command,
    myapp,
    app_requirements_path,
    app_requirements_path_index,
    mock_now,
):
    """If an app has no requirements, a requirements file is still written."""
    myapp.requires = None

    # Install requirements into the bundle
    create_command.install_app_requirements(myapp)

    # requirements.txt doesn't exist either
    assert app_requirements_path.exists()
    with app_requirements_path.open(encoding="utf-8") as f:
        assert f.read() == f"{GENERATED_DATETIME}\n"

    # Original app definitions haven't changed
    assert myapp.requires is None
    assert myapp.test_requires is None


def test_app_requirements_empty_requires(
    create_command,
    myapp,
    app_requirements_path,
    app_requirements_path_index,
    mock_now,
):
    """If an app has an empty requirements list, a requirements file is still
    written."""
    myapp.requires = []

    # Install requirements into the bundle
    create_command.install_app_requirements(myapp)

    # requirements.txt doesn't exist either
    assert app_requirements_path.exists()
    with app_requirements_path.open(encoding="utf-8") as f:
        assert f.read() == f"{GENERATED_DATETIME}\n"

    # Original app definitions haven't changed
    assert myapp.requires == []
    assert myapp.test_requires is None


def test_app_requirements_requires(
    create_command,
    myapp,
    app_requirements_path,
    app_requirements_path_index,
    mock_now,
):
    """If an app has an empty requirements list, a requirements file is still
    written."""
    myapp.requires = ["first", "second==1.2.3", "third>=3.2.1"]

    # Install requirements into the bundle
    create_command.install_app_requirements(myapp)

    # requirements.txt doesn't exist either
    assert app_requirements_path.exists()
    with app_requirements_path.open(encoding="utf-8") as f:
        assert f.read() == f"{GENERATED_DATETIME}\nfirst\nsecond==1.2.3\nthird>=3.2.1\n"

    # Original app definitions haven't changed
    assert myapp.requires == ["first", "second==1.2.3", "third>=3.2.1"]
    assert myapp.test_requires is None


def test_app_requirements_requirement_installer_args_no_template_support(
    create_command,
    myapp,
    app_path,
    app_requirements_path,
    mock_now,
    app_requirements_path_index,
):
    """If an app has requirement install args, a requirements file is still written,
    but no requirement installer args file is written if the template does not support it.
    """
    myapp.requirement_installer_args = ["--no-cache"]
    myapp.requires = ["my-favourite-package"]

    # Install requirements into the bundle
    create_command.install_app_requirements(myapp)

    # requirements.txt exists either
    assert app_requirements_path.exists()
    with app_requirements_path.open(encoding="utf-8") as f:
        assert f.read() == f"{GENERATED_DATETIME}\nmy-favourite-package\n"

    # Original app definitions haven't changed
    assert myapp.requires == ["my-favourite-package"]
    assert myapp.test_requires is None


def test_app_requirements_requirement_installer_args_with_template_support(
    create_command,
    myapp,
    app_path,
    app_requirements_path,
    app_requirement_installer_args_path,
    mock_now,
    app_requirement_installer_args_path_index,
):
    """If an app has requirement install args, a requirements file is still written,
    and requirement installer args file is written if the template supports it."""
    myapp.requirement_installer_args = ["--no-cache", "-f", "wheels with space"]
    myapp.requires = ["my-favourite-package"]

    # Install requirements into the bundle
    create_command.install_app_requirements(myapp)

    # requirements.txt exists either
    assert app_requirements_path.exists()
    with app_requirements_path.open(encoding="utf-8") as f:
        assert f.read() == f"{GENERATED_DATETIME}\nmy-favourite-package\n"

    assert app_requirement_installer_args_path.exists()
    assert (
        app_requirement_installer_args_path.read_text(encoding="utf-8")
        == "--no-cache\n-f\nwheels with space\n"
    )

    # Original app definitions haven't changed
    assert myapp.requires == ["my-favourite-package"]
    assert myapp.test_requires is None


def test_app_requirements_requirement_installer_args_without_requires_no_template_support(
    create_command,
    myapp,
    app_path,
    app_requirements_path,
    app_requirement_installer_args_path,
    mock_now,
    app_requirements_path_index,
):
    """If an app has requirement install args and no requires,
    a requirements file is still written with the timestamp,
    and does not write a requirement installer args file."""
    myapp.requirement_installer_args = ["--no-cache"]
    myapp.requires = []

    # Install requirements into the bundle
    create_command.install_app_requirements(myapp)

    # requirements.txt exists either
    assert app_requirements_path.exists()
    with app_requirements_path.open(encoding="utf-8") as f:
        assert f.read() == f"{GENERATED_DATETIME}\n"

    assert not app_requirement_installer_args_path.exists()

    # Original app definitions haven't changed
    assert myapp.requires == []
    assert myapp.test_requires is None


def test_app_requirements_requirement_installer_args_without_requires_with_template_support(
    create_command,
    myapp,
    app_path,
    app_requirements_path,
    app_requirement_installer_args_path,
    mock_now,
    app_requirement_installer_args_path_index,
):
    """If an app has requirement install args and no requires,
    a requirements file is still written with the timestamp,
    as well as requirement installer args file when the template supports it."""
    myapp.requirement_installer_args = ["--no-cache", "-f", "wheels with space"]
    myapp.requires = []

    # Install requirements into the bundle
    create_command.install_app_requirements(myapp)

    # requirements.txt exists either
    assert app_requirements_path.exists()
    with app_requirements_path.open(encoding="utf-8") as f:
        assert f.read() == f"{GENERATED_DATETIME}\n"

    assert app_requirement_installer_args_path.exists()
    assert (
        app_requirement_installer_args_path.read_text(encoding="utf-8")
        == "--no-cache\n-f\nwheels with space\n"
    )

    # Original app definitions haven't changed
    assert myapp.requires == []
    assert myapp.test_requires is None


@pytest.mark.parametrize(
    "altsep, requirement, expected",
    [
        (None, "asdf/xcvb", True),
        (None, "asdf>xcvb", False),
        (">", "asdf/xcvb", True),
        (">", "asdf>xcvb", True),
        (">", "asdf+xcvb", False),
    ],
)
def test__is_local_path_altsep_respected(
    altsep,
    requirement,
    expected,
    monkeypatch,
):
    """``os.altsep`` is included as a separator when available."""
    monkeypatch.setattr(os, "sep", "/")
    monkeypatch.setattr(os, "altsep", altsep)
    assert _is_local_path(requirement) is expected


def _test_app_requirements_paths(
    create_command,
    myapp,
    app_requirements_path,
    tmp_path,
    requirement,
):
    """A utility method that can be used to test expansion of a specific requirement."""
    if isinstance(requirement, tuple):
        requirement, converted = requirement
    else:
        converted = requirement
    myapp.requires = ["first", requirement, "third"]

    create_command.install_app_requirements(myapp)
    with app_requirements_path.open(encoding="utf-8") as f:
        assert f.read() == (
            "\n".join(
                [
                    GENERATED_DATETIME,
                    "first",
                    converted.format(tmp_path),
                    "third",
                ]
            )
            + "\n"
        )

    # Original app definitions haven't changed
    assert myapp.requires == ["first", requirement, "third"]
    assert myapp.test_requires is None


@pytest.mark.parametrize(
    "requirement",
    [
        # Simple PyPI package references
        "my-package",
        "my-package==1.2.3",
        "my-package<=1.2.3",
        # More complex PyPI references
        "my-package[optional]<=1.2.3",
        "my-package[optional]<=1.2.3; python_version<3.7",
        # References to git packages
        "git+https://github.com/project/package",
        "git+https://github.com/project/package#egg=my-package",
        "git+https://github.com/project/package@deadbeef#egg=my-package",
        "git+https://github.com/project/package@some-branch#egg=my-package",
        # URL references to wheels
        "http://example.com/path/to/mypackage-1.2.3-py3-none-any.whl",
        "https://example.com/path/to/mypackage-1.2.3-py3-none-any.whl",
        # Zip file source installs
        "my-package @ https://example.com/path/to/1.2.3.zip",
    ],
)
def test_app_requirements_non_paths(
    create_command,
    myapp,
    app_requirements_path,
    app_requirements_path_index,
    tmp_path,
    requirement,
    mock_now,
):
    """Requirements which are not paths are left unchanged."""
    _test_app_requirements_paths(
        create_command,
        myapp,
        app_requirements_path,
        tmp_path,
        requirement,
    )


@pytest.mark.skipif(os.name != "posix", reason="Unix specific tests")
@pytest.mark.parametrize(
    "requirement",
    [
        # A reference that involves an absolute path
        "/absolute/path/to/package",
        # Relative paths.
        ("./package/inside/project", "{}/base_path/package/inside/project"),
        ("../package/outside/project", "{}/package/outside/project"),
        ("sub/package/inside/project", "{}/base_path/sub/package/inside/project"),
    ],
)
def test_app_requirements_paths_unix(
    create_command,
    myapp,
    app_requirements_path,
    app_requirements_path_index,
    tmp_path,
    requirement,
    mock_now,
):
    """Requirement paths in Unix format are expanded correctly."""
    _test_app_requirements_paths(
        create_command,
        myapp,
        app_requirements_path,
        tmp_path,
        requirement,
    )


@pytest.mark.skipif(os.name != "nt", reason="Windows specific tests")
@pytest.mark.parametrize(
    "requirement",
    [
        # A reference that involves an absolute path
        r"C:\absolute\path\to\package",
        ("C:/absolute/path/to/package", r"C:\absolute\path\to\package"),
        ("/absolute/path/to/package", r"C:\absolute\path\to\package"),
        # Relative paths using forward slash separators
        ("./package/inside/project", r"{}\base_path\package\inside\project"),
        ("../package/outside/project", r"{}\package\outside\project"),
        ("sub/package/inside/project", r"{}\base_path\sub\package\inside\project"),
        # Relative paths using backslash separators
        (r".\package\inside\project", r"{}\base_path\package\inside\project"),
        (r"..\package\outside\project", r"{}\package\outside\project"),
        (r"sub\package\inside\project", r"{}\base_path\sub\package\inside\project"),
    ],
)
def test_app_requirements_paths_windows(
    create_command,
    myapp,
    app_requirements_path,
    app_requirements_path_index,
    tmp_path,
    requirement,
    mock_now,
):
    """Requirement paths in Windows format are expanded correctly."""
    _test_app_requirements_paths(
        create_command,
        myapp,
        app_requirements_path,
        tmp_path,
        requirement,
    )


def test_app_packages_test_requires(
    create_command,
    myapp,
    app_packages_path,
    app_packages_path_index,
):
    """If an app has test requirements, they're not included unless we are in test
    mode."""
    myapp.requires = ["first", "second==1.2.3", "third>=3.2.1"]
    myapp.test_requires = ["pytest", "pytest-tldr"]

    create_command.install_app_requirements(myapp)

    # A request was made to install requirements
    create_command.tools[myapp].app_context.run.assert_called_with(
        [
            sys.executable,
            "-u",
            "-X",
            "utf8",
            "-m",
            "pip",
            "install",
            "--disable-pip-version-check",
            "--upgrade",
            "--no-user",
            f"--target={app_packages_path}",
            "first",
            "second==1.2.3",
            "third>=3.2.1",
        ],
        check=True,
        encoding="UTF-8",
    )

    # Original app definitions haven't changed
    assert myapp.requires == ["first", "second==1.2.3", "third>=3.2.1"]
    assert myapp.test_requires == ["pytest", "pytest-tldr"]


def test_app_packages_test_requires_test_mode(
    create_command,
    myapp,
    app_packages_path,
    app_packages_path_index,
):
    """If an app has test requirements and we're in test mode, they are installed."""
    myapp.requires = ["first", "second==1.2.3", "third>=3.2.1"]
    myapp.test_requires = ["pytest", "pytest-tldr"]
    myapp.test_mode = True

    create_command.install_app_requirements(myapp)

    # A request was made to install requirements
    create_command.tools[myapp].app_context.run.assert_called_with(
        [
            sys.executable,
            "-u",
            "-X",
            "utf8",
            "-m",
            "pip",
            "install",
            "--disable-pip-version-check",
            "--upgrade",
            "--no-user",
            f"--target={app_packages_path}",
            "first",
            "second==1.2.3",
            "third>=3.2.1",
            "pytest",
            "pytest-tldr",
        ],
        check=True,
        encoding="UTF-8",
    )

    # Original app definitions haven't changed
    assert myapp.requires == ["first", "second==1.2.3", "third>=3.2.1"]
    assert myapp.test_requires == ["pytest", "pytest-tldr"]


def test_app_packages_only_test_requires_test_mode(
    create_command,
    myapp,
    app_packages_path,
    app_packages_path_index,
):
    """If an app only has test requirements and we're in test mode, they are
    installed."""
    myapp.requires = None
    myapp.test_requires = ["pytest", "pytest-tldr"]
    myapp.test_mode = True

    create_command.install_app_requirements(myapp)

    # A request was made to install requirements
    create_command.tools[myapp].app_context.run.assert_called_with(
        [
            sys.executable,
            "-u",
            "-X",
            "utf8",
            "-m",
            "pip",
            "install",
            "--disable-pip-version-check",
            "--upgrade",
            "--no-user",
            f"--target={app_packages_path}",
            "pytest",
            "pytest-tldr",
        ],
        check=True,
        encoding="UTF-8",
    )

    # Original app definitions haven't changed
    assert myapp.requires is None
    assert myapp.test_requires == ["pytest", "pytest-tldr"]
