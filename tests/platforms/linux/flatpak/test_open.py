import os
import sys
from unittest.mock import MagicMock

import pytest

from briefcase.console import Console, Log
from briefcase.integrations.subprocess import Subprocess
from briefcase.platforms.linux.flatpak import LinuxFlatpakOpenCommand

from ....utils import create_file


@pytest.fixture
def open_command(tmp_path, first_app_config):
    command = LinuxFlatpakOpenCommand(
        logger=Log(),
        console=Console(),
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )
    command.tools.os = MagicMock(spec_set=os)
    command.tools.subprocess = MagicMock(spec_set=Subprocess)

    # Mock the call to verify the existence of the flatpak tools
    command.tools.subprocess.check_output.side_effect = [
        # flatpak --version
        "1.2.3",
        # flatpak-builder --version
        "1.2.3",
    ]

    return command


@pytest.mark.skipif(sys.platform != "linux", reason="Linux specific test")
def test_open(open_command, first_app_config, tmp_path):
    """On Linux, Open run `xdg-open` on the Content folder."""
    # Create the flatpak manifest file that would be in the project bundle.
    create_file(
        open_command.project_path(first_app_config) / "manifest.yml",
        "Flatpak manifest",
    )

    open_command(first_app_config)

    open_command.tools.subprocess.Popen.assert_called_once_with(
        [
            "xdg-open",
            tmp_path / "base_path" / "linux" / "flatpak" / "First App",
        ]
    )
