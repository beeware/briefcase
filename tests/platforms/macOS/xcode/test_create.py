import sys
from unittest import mock

import pytest

from briefcase.platforms.macOS.xcode import macOSXcodeCreateCommand


@pytest.fixture
def create_command(dummy_console, mock_other_venv, tmp_path):
    command = macOSXcodeCreateCommand(
        console=dummy_console,
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )

    command.generate_template = mock.MagicMock()
    command.verify_not_on_icloud = mock.MagicMock()
    command.create_app_environment = mock.MagicMock(return_value=mock_other_venv)
    command.tools.sys = mock.MagicMock(spec_set=sys)
    command.tools.sys.version_info = (3, "X", 0)

    return command
