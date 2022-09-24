from unittest import mock

import pytest

from briefcase.console import Console, Log
from briefcase.platforms.macOS.app import macOSAppBuildCommand


@pytest.fixture
def build_command(tmp_path):
    command = macOSAppBuildCommand(
        logger=Log(),
        console=Console(),
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )

    command.select_identity = mock.MagicMock()
    command.sign_app = mock.MagicMock()
    command.sign_file = mock.MagicMock()

    return command


def test_build_app(build_command, first_app_with_binaries):
    """A macOS App is adhoc signed as part of the build process."""
    # Build the app
    build_command.build_app(first_app_with_binaries)

    # A request has been made to sign the app
    build_command.sign_app.assert_called_once_with(
        app=first_app_with_binaries,
        identity="-",
    )

    # No request to select a signing identity was made
    build_command.select_identity.assert_not_called()

    # No attempt was made to sign a specific file;
    # This ignores the calls that would have been made transitively
    # by calling sign_app()
    build_command.sign_file.assert_not_called()
