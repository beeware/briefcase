import sys
from subprocess import CalledProcessError
from unittest.mock import MagicMock

import pytest

from briefcase.console import LogLevel
from briefcase.exceptions import RequirementsInstallError


@pytest.mark.parametrize("logging_level", [LogLevel.INFO, LogLevel.DEEP_DEBUG])
def test_install_requirements_no_error(dev_command, first_app, logging_level):
    """Ensure run is executed properly to install requirements."""
    # Configure logging level
    dev_command.console.verbosity = logging_level

    first_app.requires = [
        "package-one",
        "./local",
        "package_two",
    ]

    mock_venv = MagicMock()
    dev_command.install_dev_requirements(app=first_app, venv=mock_venv)

    mock_venv.run.assert_called_once_with(
        [
            sys.executable,
            "-u",
            "-X",
            "utf8",
            "-m",
            "pip",
            "install",
            "--upgrade",
        ]
        + (["-vv"] if logging_level == LogLevel.DEEP_DEBUG else [])
        + [
            "package-one",
            "-e",
            "./local",
            "package_two",
        ],
        check=True,
        encoding="UTF-8",
    )


@pytest.mark.parametrize(
    ("requirement", "editable"),
    (
        [
            # Relative paths and single level
            ("./current-dir", True),
            ("../parent-dir", True),
            # Relative paths and multiple levels
            ("../../grandparent/package", True),
            ("./deeply/nested/package", True),
            ("../sibling/package", True),
            # Simple relative paths
            ("folder/package", True),
            ("src/mypackage", True),
            # Absolute paths
            ("/absolute/path", True),
            # SCM URLs (should NOT get -e for now):
            ("git+https://github.com/user/repo.git", False),
            ("git+ssh://git@github.com/user/repo.git", False),
            ("hg+https://bitbucket.org/user/repo", False),
            ("git+https://github.com/user/repo.git@1.2.3", False),
            ("SomeProject@git+https://github.com/user/repo.git", False),
            ("SomeProject@git+https://github.com/user/repo.git@branch", False),
            (
                "SomeProject@git+https://github.com/user/repo.git#subdirectory=sub_dir",
                False,
            ),
            # Archives (should NOT get -e):
            ("./local/package.tar.gz", False),
            ("./local/package.zip", False),
            ("./local/package.whl", False),
            ("./local/package.tar.bz2", False),
            ("./local/package.tar", False),
            # Archives specified by URL
            ("https://github.com/user/repo/archive/main.tar.gz", False),
            ("SomeProject@https://github.com/user/repo/archive/main.tar.gz", False),
            ("https://files.pythonhosted.org/packages/.../package-1.0.tar.gz", False),
            # Regular packages (should NOT get -e):
            ("package1", False),
            ("package2==1.2.3", False),
            ("package3 == 2.3.4", False),
            ("package4 >= 3.4.5", False),
        ]
        + (
            [
                # Windows paths. Windows honors unix-style paths, but on Unix,
                # windows-style paths appear as package names, so we only test
                # this option on Windows.
                ("folder\\windows", True),
                (".\\windows\\current", True),
                ("..\\windows\\parent", True),
                ("C:\\absolute\\windows", True),
            ]
            if sys.platform == "win32"
            else []
        )
    ),
)
def test_install_requirements_path_formats(
    dev_command,
    first_app,
    requirement,
    editable,
):
    """Test possible path formats that pip supports for editable installation."""
    first_app.requires = [requirement]

    mock_venv = MagicMock()
    dev_command.install_dev_requirements(app=first_app, venv=mock_venv)

    mock_venv.run.assert_called_once_with(
        [
            sys.executable,
            "-u",
            "-X",
            "utf8",
            "-m",
            "pip",
            "install",
            "--upgrade",
        ]
        + (["-e"] if editable else [])
        + [
            requirement,
        ],
        check=True,
        encoding="UTF-8",
    )


def test_install_requirements_error(dev_command, first_app):
    """Ensure RequirementsInstallError exception is raised for install errors."""
    first_app.requires = ["package-one", "package_two", "packagethree"]

    mock_venv = MagicMock()
    mock_venv.run.side_effect = CalledProcessError(returncode=-1, cmd="pip")

    with pytest.raises(
        RequirementsInstallError,
        match=r"Unable to install requirements\.",
    ):
        dev_command.install_dev_requirements(app=first_app, venv=mock_venv)

    mock_venv.run.assert_called_once_with(
        [
            sys.executable,
            "-u",
            "-X",
            "utf8",
            "-m",
            "pip",
            "install",
            "--upgrade",
            "package-one",
            "package_two",
            "packagethree",
        ],
        check=True,
        encoding="UTF-8",
    )


def test_no_requirements(dev_command, first_app):
    """Ensure dependency installation is not attempted when nothing to install."""
    first_app.requires = []

    mock_venv = MagicMock()
    dev_command.install_dev_requirements(app=first_app, venv=mock_venv)

    mock_venv.run.assert_not_called()


def test_no_requirements_with_requirement_installer_Args(dev_command, first_app):
    """Ensure dependency installation is not attempted when nothing to install, even if
    requirement installer args are defined."""
    first_app.requires = []
    first_app.requirement_installer_args = ["--no-cache"]

    mock_venv = MagicMock()
    dev_command.install_dev_requirements(app=first_app, venv=mock_venv)

    mock_venv.run.assert_not_called()


def test_install_requirements_test_mode(dev_command, first_app):
    """If an app has test requirements, they are also installed."""
    first_app.requires = ["package-one", "package_two", "packagethree"]
    first_app.test_requires = ["test-one", "test_two", "./local1"]

    mock_venv = MagicMock()
    dev_command.install_dev_requirements(app=first_app, venv=mock_venv)

    mock_venv.run.assert_called_once_with(
        [
            sys.executable,
            "-u",
            "-X",
            "utf8",
            "-m",
            "pip",
            "install",
            "--upgrade",
            "package-one",
            "package_two",
            "packagethree",
            "test-one",
            "test_two",
            "-e",
            "./local1",
        ],
        check=True,
        encoding="UTF-8",
    )


def test_only_test_requirements(dev_command, first_app):
    """If an app only has test requirements, they're installed correctly."""
    first_app.requires = None
    first_app.test_requires = ["test-one", "test_two", "./local1"]

    mock_venv = MagicMock()
    dev_command.install_dev_requirements(app=first_app, venv=mock_venv)

    mock_venv.run.assert_called_once_with(
        [
            sys.executable,
            "-u",
            "-X",
            "utf8",
            "-m",
            "pip",
            "install",
            "--upgrade",
            "test-one",
            "test_two",
            "-e",
            "./local1",
        ],
        check=True,
        encoding="UTF-8",
    )


def test_requirement_installer_args(dev_command, first_app):
    """If an app has requirement installer args, they're used correctly."""
    first_app.requires = ["one", "two", "./local1"]
    first_app.requirement_installer_args = ["--no-cache"]

    mock_venv = MagicMock()
    dev_command.install_dev_requirements(app=first_app, venv=mock_venv)

    mock_venv.run.assert_called_once_with(
        [
            sys.executable,
            "-u",
            "-X",
            "utf8",
            "-m",
            "pip",
            "install",
            "--upgrade",
            "one",
            "two",
            "-e",
            "./local1",
            "--no-cache",
        ],
        check=True,
        encoding="UTF-8",
    )
