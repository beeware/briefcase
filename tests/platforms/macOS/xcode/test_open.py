import os
import subprocess
import sys
from unittest.mock import MagicMock

import pytest

from briefcase.console import Console, Log
from briefcase.integrations.subprocess import Subprocess
from briefcase.platforms.macOS.xcode import macOSXcodeOpenCommand

from ....utils import create_file


@pytest.fixture
def open_command(tmp_path, first_app_config):
    command = macOSXcodeOpenCommand(
        logger=Log(),
        console=Console(),
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )
    command.tools.os = MagicMock(spec_set=os)
    command.tools.subprocess = MagicMock(spec_set=Subprocess)

    # Mock the call to verify the existence of the cmdline tools
    command.tools.subprocess.check_output.side_effect = [
        # xcode-select -p
        "/Applications/Xcode.app/Contents/Developer",
        # xcodebuild -version
        "Xcode 13.0.0",
        # xcode-select  --install
        subprocess.CalledProcessError(cmd=["xcode-select", "--install"], returncode=1),
        # /usr/bin/clang --version
        "Apple clang version 13.1.6 (clang-1316.0.21.2.5)\n...",
    ]
    return command


@pytest.mark.skipif(sys.platform != "darwin", reason="macOS specific test")
def test_open(open_command, first_app_config, tmp_path):
    """On macOS, Open starts Xcode on the project."""
    # Create the project file to mock a created project.
    create_file(
        open_command.project_path(first_app_config) / "project.pbxproj",
        "Xcode project",
    )

    open_command(first_app_config)

    open_command.tools.subprocess.Popen.assert_called_once_with(
        [
            "open",
            tmp_path
            / "base_path"
            / "macOS"
            / "Xcode"
            / "First App"
            / "First App.xcodeproj",
        ]
    )
