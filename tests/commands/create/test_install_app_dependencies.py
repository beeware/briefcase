import subprocess
import sys

import pytest

from briefcase.commands.create import DependencyInstallError


def test_no_requires(create_command, myapp, app_packages_path):
    "If an app has no requirements, install_app_dependencies is a no-op."
    myapp.requires = None

    create_command.install_app_dependencies(myapp)

    # No request was made to install dependencies
    create_command.subprocess.run.assert_not_called()


def test_empty_requires(create_command, myapp, app_packages_path):
    "If an app has an empty requirements list, install_app_dependencies is a no-op."
    myapp.requires = []

    create_command.install_app_dependencies(myapp)

    # No request was made to install dependencies
    create_command.subprocess.run.assert_not_called()


def test_valid_requires(create_command, myapp, app_packages_path):
    "If an app has an valid list of requirements, pip is invoked."
    myapp.requires = ['first', 'second', 'third']

    create_command.install_app_dependencies(myapp)

    # No request was made to install dependencies
    create_command.subprocess.run.assert_called_with(
        [
            sys.executable,
            "-m",
            "pip", "install",
            "--upgrade",
            '--target={}'.format(app_packages_path),
            'first',
            'second',
            'third',
        ],
        check=True,
    )


def test_invalid_requires(create_command, myapp, app_packages_path):
    "If an app has an valid list of requirements, pip is invoked."
    myapp.requires = ['does-not-exist']

    # Unfortunately, no way to tell the difference between "offline" and
    # "your requirements are invalid"; pip returns status code 1 for all
    # failures.
    create_command.subprocess.run.side_effect = subprocess.CalledProcessError(
        cmd=['python', '-m', 'pip', '...'],
        returncode=1
    )

    with pytest.raises(DependencyInstallError):
        create_command.install_app_dependencies(myapp)

    # But the request to install was still made
    create_command.subprocess.run.assert_called_with(
        [
            sys.executable,
            "-m",
            "pip", "install",
            "--upgrade",
            '--target={}'.format(app_packages_path),
            'does-not-exist',
        ],
        check=True,
    )


def test_offline(create_command, myapp, app_packages_path):
    "If user is offline, pip fails."
    myapp.requires = ['first', 'second', 'third']

    # Unfortunately, no way to tell the difference between "offline" and
    # "your requirements are invalid"; pip returns status code 1 for all
    # failures.
    create_command.subprocess.run.side_effect = subprocess.CalledProcessError(
        cmd=['python', '-m', 'pip', '...'],
        returncode=1
    )

    with pytest.raises(DependencyInstallError):
        create_command.install_app_dependencies(myapp)

    # But the request to install was still made
    create_command.subprocess.run.assert_called_with(
        [
            sys.executable,
            "-m",
            "pip", "install",
            "--upgrade",
            '--target={}'.format(app_packages_path),
            'first',
            'second',
            'third',
        ],
        check=True,
    )
