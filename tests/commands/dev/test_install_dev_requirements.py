import sys
from subprocess import CalledProcessError

import pytest

from briefcase.console import LogLevel
from briefcase.exceptions import RequirementsInstallError


@pytest.mark.parametrize("logging_level", [LogLevel.INFO, LogLevel.DEEP_DEBUG])
def test_install_requirements_no_error(dev_command, first_app, logging_level):
    """Ensure run is executed properly to install requirements."""
    # Configure logging level
    dev_command.console.verbosity = logging_level

    first_app.requires = ["package-one", "package_two", "packagethree"]

    dev_command.install_dev_requirements(app=first_app)

    dev_command.tools.subprocess.run.assert_called_once_with(
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
        + ["package-one", "package_two", "packagethree"],
        check=True,
        encoding="UTF-8",
    )


def test_install_requirements_error(dev_command, first_app):
    """Ensure RequirementsInstallError exception is raised for install errors."""
    first_app.requires = ["package-one", "package_two", "packagethree"]

    dev_command.tools.subprocess.run.side_effect = CalledProcessError(
        returncode=-1, cmd="pip"
    )

    with pytest.raises(
        RequirementsInstallError,
        match="Unable to install requirements.",
    ):
        dev_command.install_dev_requirements(app=first_app)

    dev_command.tools.subprocess.run.assert_called_once_with(
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

    dev_command.install_dev_requirements(app=first_app)

    dev_command.tools.subprocess.run.assert_not_called()


def test_no_requirements_with_requirement_installer_Args(dev_command, first_app):
    """Ensure dependency installation is not attempted when nothing to install,
    even if requirement installer args are defined."""
    first_app.requires = []
    first_app.requirement_installer_args = ["--no-cache"]

    dev_command.install_dev_requirements(app=first_app)

    dev_command.tools.subprocess.run.assert_not_called()


def test_install_requirements_test_mode(dev_command, first_app):
    """If an app has test requirements, they are also installed."""
    first_app.requires = ["package-one", "package_two", "packagethree"]
    first_app.test_requires = ["test-one", "test_two"]

    dev_command.install_dev_requirements(app=first_app)

    dev_command.tools.subprocess.run.assert_called_once_with(
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
        ],
        check=True,
        encoding="UTF-8",
    )


def test_only_test_requirements(dev_command, first_app):
    """If an app only has test requirements, they're installed correctly."""
    first_app.requires = None
    first_app.test_requires = ["test-one", "test_two"]

    dev_command.install_dev_requirements(app=first_app)

    dev_command.tools.subprocess.run.assert_called_once_with(
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
        ],
        check=True,
        encoding="UTF-8",
    )


def test_requirement_installer_args(dev_command, first_app):
    """If an app has requirement installer args, they're used correctly."""
    first_app.requires = ["one", "two"]
    first_app.requirement_installer_args = ["--no-cache"]

    dev_command.install_dev_requirements(app=first_app)

    dev_command.tools.subprocess.run.assert_called_once_with(
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
            "--no-cache",
        ],
        check=True,
        encoding="UTF-8",
    )
