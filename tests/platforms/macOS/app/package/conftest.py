from unittest import mock

import pytest

from briefcase.console import Console
from briefcase.integrations.subprocess import Subprocess
from briefcase.platforms.macOS.app import macOSAppPackageCommand


@pytest.fixture
def package_command(tmp_path):
    command = macOSAppPackageCommand(
        console=Console(),
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )

    command.select_identity = mock.MagicMock()
    command.sign_app = mock.MagicMock()
    command.sign_file = mock.MagicMock()
    command.notarize = mock.MagicMock()
    command.dmgbuild = mock.MagicMock()
    command.tools.subprocess = mock.MagicMock(spec=Subprocess)
    command.verify_not_on_icloud = mock.MagicMock()

    return command
