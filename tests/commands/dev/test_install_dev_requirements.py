from unittest.mock import MagicMock

import pytest

from briefcase.console import LogLevel


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

    mock_venv.install_requirements.assert_called_once_with(
        [
            "package-one",
            "./local",
            "package_two",
        ],
        allow_editable=True,
        installer_args=[],
    )


def test_no_requirements(dev_command, first_app):
    """Ensure dependency installation is not attempted when nothing to install."""
    first_app.requires = []

    mock_venv = MagicMock()
    dev_command.install_dev_requirements(app=first_app, venv=mock_venv)

    mock_venv.install_requirements.assert_not_called()


def test_no_requirements_with_requirement_installer_Args(dev_command, first_app):
    """Ensure dependency installation is not attempted when nothing to install, even if
    requirement installer args are defined."""
    first_app.requires = []
    first_app.requirement_installer_args = ["--no-cache"]

    mock_venv = MagicMock()
    dev_command.install_dev_requirements(app=first_app, venv=mock_venv)

    mock_venv.install_requirements.assert_not_called()


def test_install_requirements_test_mode(dev_command, first_app):
    """If an app has test requirements, they are also installed."""
    first_app.requires = ["package-one", "package_two", "packagethree"]
    first_app.test_requires = ["test-one", "test_two", "./local1"]

    mock_venv = MagicMock()
    dev_command.install_dev_requirements(app=first_app, venv=mock_venv)

    mock_venv.install_requirements.assert_called_once_with(
        [
            "package-one",
            "package_two",
            "packagethree",
            "test-one",
            "test_two",
            "./local1",
        ],
        allow_editable=True,
        installer_args=[],
    )


def test_only_test_requirements(dev_command, first_app):
    """If an app only has test requirements, they're installed correctly."""
    first_app.requires = None
    first_app.test_requires = ["test-one", "test_two", "./local1"]

    mock_venv = MagicMock()
    dev_command.install_dev_requirements(app=first_app, venv=mock_venv)

    mock_venv.install_requirements.assert_called_once_with(
        ["test-one", "test_two", "./local1"],
        allow_editable=True,
        installer_args=[],
    )


def test_requirement_installer_args(dev_command, first_app):
    """If an app has requirement installer args, they're used correctly."""
    first_app.requires = ["one", "two", "./local1"]
    first_app.requirement_installer_args = ["--no-cache"]

    mock_venv = MagicMock()
    dev_command.install_dev_requirements(app=first_app, venv=mock_venv)

    mock_venv.install_requirements.assert_called_once_with(
        ["one", "two", "./local1"],
        allow_editable=True,
        installer_args=["--no-cache"],
    )
