import sys
from subprocess import CalledProcessError

import pytest

from briefcase.commands.create import RequirementsInstallError


def test_install_requirements_no_error(dev_command, first_app):
    """Ensure run is executed properly to install requirements."""
    first_app.requires = ["package-one", "package_two", "packagethree"]

    dev_command.install_dev_requirements(app=first_app)

    dev_command.tools.subprocess.run.assert_called_once_with(
        [
            sys.executable,
            "-u",
            "-m",
            "pip",
            "install",
            "--upgrade",
            "package-one",
            "package_two",
            "packagethree",
        ],
        check=True,
    )


def test_install_requirements_error(dev_command, first_app):
    """Ensure RequirementsInstallError exception is raised for install
    errors."""
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
            "-m",
            "pip",
            "install",
            "--upgrade",
            "package-one",
            "package_two",
            "packagethree",
        ],
        check=True,
    )


def test_no_requirements(dev_command, first_app):
    """Ensure dependency installation is not attempted when nothing to
    install."""
    first_app.requires = []

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
            "-m",
            "pip",
            "install",
            "--upgrade",
            "test-one",
            "test_two",
        ],
        check=True,
    )
