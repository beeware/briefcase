import os
import sys
from unittest.mock import MagicMock

import pytest

from briefcase.console import Console, Log
from briefcase.integrations.subprocess import Subprocess
from briefcase.platforms.linux.appimage import LinuxAppImageOpenCommand

from ....utils import create_file


@pytest.fixture
def open_command(tmp_path, first_app_config):
    command = LinuxAppImageOpenCommand(
        logger=Log(),
        console=Console(),
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )
    command.tools.os = MagicMock(spec_set=os)
    command.tools.subprocess = MagicMock(spec_set=Subprocess)

    return command


@pytest.mark.skipif(sys.platform != "linux", reason="Linux specific test")
def test_open(open_command, first_app_config, tmp_path):
    """On Linux, Open runs `xdg-open` on the project folder."""
    # Create the desktop file that would be in the project folder.
    create_file(
        open_command.project_path(first_app_config)
        / "First App.AppDir"
        / "com.example.firstapp.desktop",
        "FreeDesktop file",
    )

    open_command(first_app_config)

    open_command.tools.subprocess.Popen.assert_called_once_with(
        [
            "xdg-open",
            tmp_path / "base_path" / "linux" / "appimage" / "First App",
        ]
    )
