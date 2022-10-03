import sys
from subprocess import CalledProcessError

import pytest

from briefcase.commands.create import DependencyInstallError


def test_install_dependencies_no_error(dev_command, first_app):
    """Ensure run is executed properly to install dependencies."""
    first_app.requires = ["package-one", "package_two", "packagethree"]

    dev_command.install_dev_dependencies(app=first_app)

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


def test_install_dependencies_error(dev_command, first_app):
    """Ensure DependencyInstallError exception is raised for install errors."""
    first_app.requires = ["package-one", "package_two", "packagethree"]

    dev_command.tools.subprocess.run.side_effect = CalledProcessError(
        returncode=-1, cmd="pip"
    )

    with pytest.raises(DependencyInstallError, match="Unable to install dependencies."):
        dev_command.install_dev_dependencies(app=first_app)

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


def test_no_dependencies(dev_command, first_app):
    """Ensure dependency installation is not attempted when nothing to
    install."""
    first_app.requires = []

    dev_command.install_dev_dependencies(app=first_app)

    dev_command.tools.subprocess.run.assert_not_called()
