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


def test_install_requirements_path_formats(dev_command, first_app):
    """Test possible path formats that pip supports for editable installation."""
    first_app.requires = [
        # Relative paths and single level
        "./current-dir",
        "../parent-dir",
        # Relative paths and multiple levels
        "../../grandparent/package",
        "./deeply/nested/package",
        "../sibling/package",
        # Simple relative paths
        "folder/package",
        "src/mypackage",
        # Absolute paths
        "/absolute/path",
        # Windows paths
        "folder\\windows",
        ".\\windows\\current",
        "..\\windows\\parent",
        "C:\\absolute\\windows",
        # SCM URLs (should NOT get -e for now):
        "git+https://github.com/user/repo.git",
        "git+ssh://git@github.com/user/repo.git",
        "hg+https://bitbucket.org/user/repo",
        # Tarballs (should NOT get -e):
        "./local/package.tar.gz",
        "./local/package.zip",
        "./local/package.whl",
        "./local/package.tar.bz2",
        "./local/package.tar",
        "https://github.com/user/repo/archive/main.tar.gz",
        "https://files.pythonhosted.org/packages/.../package-1.0.tar.gz",
        # Regular packages (should NOT get -e):
        "package1",
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
            "-e",
            "./current-dir",
            "-e",
            "../parent-dir",
            "-e",
            "../../grandparent/package",
            "-e",
            "./deeply/nested/package",
            "-e",
            "../sibling/package",
            "-e",
            "folder/package",
            "-e",
            "src/mypackage",
            "-e",
            "/absolute/path",
            "-e",
            "folder\\windows",
            "-e",
            ".\\windows\\current",
            "-e",
            "..\\windows\\parent",
            "-e",
            "C:\\absolute\\windows",
            "git+https://github.com/user/repo.git",
            "git+ssh://git@github.com/user/repo.git",
            "hg+https://bitbucket.org/user/repo",
            "./local/package.tar.gz",
            "./local/package.zip",
            "./local/package.whl",
            "./local/package.tar.bz2",
            "./local/package.tar",
            "https://github.com/user/repo/archive/main.tar.gz",
            "https://files.pythonhosted.org/packages/.../package-1.0.tar.gz",
            "package1",
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
        match="Unable to install requirements.",
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
