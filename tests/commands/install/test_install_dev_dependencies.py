import sys

import pytest
from unittest import mock

from briefcase.commands import InstallCommand
from subprocess import CalledProcessError

from briefcase.commands.create import DependencyInstallError


@pytest.fixture
def install_command(tmp_path):
    command = InstallCommand(base_path=tmp_path)
    command.subprocess = mock.Mock()
    return command


def test_not_installing(install_command, first_app):
    install_command.install_dev_dependencies(first_app, False)
    install_command.subprocess.run.assert_not_called()


def test_not_installing_because_of_no_requires(install_command, first_app):
    install_command.install_dev_dependencies(first_app, True)
    install_command.subprocess.run.assert_not_called()


def test_install_because_flag(install_command, first_app):
    first_app.requires = ["a", "b", "c"]
    install_command.install_dev_dependencies(first_app, True)
    install_command.subprocess.run.assert_called_once_with(
        [sys.executable, "-m", "pip", "install", "--upgrade", "a", "b", "c"], check=True
    )


def test_install_because_not_installed(install_command, first_app_uninstalled):
    first_app_uninstalled.requires = ["a", "b", "c"]
    install_command.install_dev_dependencies(first_app_uninstalled, False)
    install_command.subprocess.run.assert_called_once_with(
        [sys.executable, "-m", "pip", "install", "--upgrade", "a", "b", "c"], check=True
    )


def test_installation_raises_error(install_command, first_app_uninstalled):
    first_app_uninstalled.requires = ["a", "b", "c"]
    install_command.subprocess.run.side_effect = CalledProcessError(1, sys.executable)
    with pytest.raises(DependencyInstallError):
        install_command.install_dev_dependencies(first_app_uninstalled, False)
    install_command.subprocess.run.assert_called_once_with(
        [sys.executable, "-m", "pip", "install", "--upgrade", "a", "b", "c"], check=True
    )
