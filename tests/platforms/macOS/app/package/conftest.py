import shutil
from unittest import mock

import pytest

from briefcase.integrations.subprocess import Subprocess
from briefcase.platforms.macOS.app import macOSAppPackageCommand


@pytest.fixture
def package_command(dummy_console, tmp_path):
    command = macOSAppPackageCommand(
        console=dummy_console,
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )

    command._command_factory = mock.MagicMock()
    command.select_identity = mock.MagicMock()
    command.sign_app = mock.MagicMock()
    command.sign_file = mock.MagicMock()
    command.notarize = mock.MagicMock()
    command.dmgbuild = mock.MagicMock()
    command.tools.subprocess = mock.MagicMock(spec=Subprocess)
    command.verify_not_on_icloud = mock.MagicMock()

    return command


@pytest.fixture
def external_first_app(first_app_with_binaries, first_app_config, tmp_path):
    # Convert the first_app_config into an external app
    first_app_config.sources = None
    first_app_config.external_package_path = (
        tmp_path / "base_path/external/First App.app"
    )

    # Move the binaries from the compiled first app to the external location
    first_app_config.external_package_path.parent.mkdir(parents=True)
    shutil.move(
        tmp_path / "base_path/build/first-app/macos/app/First App.app",
        tmp_path / "base_path/external/First App.app",
    )

    # And purge the original package path, so we have a "clean" template directory
    shutil.rmtree(tmp_path / "base_path/build/first-app/macos/app")

    return first_app_config
