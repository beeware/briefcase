import os
import sys
from unittest.mock import MagicMock

import pytest

from briefcase.console import Console, Log
from briefcase.integrations.subprocess import Subprocess
from briefcase.platforms.windows.app import WindowsAppOpenCommand


@pytest.fixture
def open_command(tmp_path, first_app_config):
    command = WindowsAppOpenCommand(
        logger=Log(),
        console=Console(),
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )
    command.tools.os = MagicMock(spec_set=os)
    command.tools.subprocess = MagicMock(spec_set=Subprocess)
    return command


@pytest.mark.skipif(sys.platform != "win32", reason="Windows specific test")
def test_open_windows(open_command, first_app_config, tmp_path):
    """On Windows, open invokes `startfile` on the project folder."""
    # Create the project folder to mock a created project.
    open_command.project_path(first_app_config).mkdir(parents=True)

    open_command(first_app_config)

    open_command.tools.os.startfile.assert_called_once_with(
        tmp_path / "base_path" / "windows" / "app" / "First App"
    )
