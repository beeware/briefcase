import os
import sys
from unittest.mock import MagicMock

import pytest

from briefcase.console import Console, Log
from briefcase.integrations.subprocess import Subprocess
from briefcase.platforms.windows.visualstudio import WindowsVisualStudioOpenCommand

from ....utils import create_file


@pytest.fixture
def open_command(tmp_path, first_app_config):
    command = WindowsVisualStudioOpenCommand(
        logger=Log(),
        console=Console(),
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )
    command.tools.os = MagicMock(spec_set=os)
    command.tools.subprocess = MagicMock(spec_set=Subprocess)
    return command


@pytest.mark.skipif(sys.platform != "win32", reason="Windows specific test")
def test_open(open_command, first_app_config, tmp_path):
    """Open command opens visual studio project file."""
    # Create the solution file that would be in the created project.
    create_file(open_command.project_path(first_app_config), "Visual Studio Solution")

    open_command(first_app_config)

    open_command.tools.os.startfile.assert_called_once_with(
        tmp_path
        / "base_path"
        / "windows"
        / "VisualStudio"
        / "First App"
        / "First App.sln"
    )
