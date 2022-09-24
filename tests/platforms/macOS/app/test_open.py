import os
import sys
from unittest.mock import MagicMock

import pytest

from briefcase.console import Console, Log
from briefcase.integrations.subprocess import Subprocess
from briefcase.platforms.macOS.app import macOSAppOpenCommand

from ....utils import create_file


@pytest.fixture
def open_command(tmp_path, first_app_config):
    command = macOSAppOpenCommand(
        logger=Log(),
        console=Console(),
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )
    command.tools.os = MagicMock(spec_set=os)
    command.tools.subprocess = MagicMock(spec_set=Subprocess)

    return command


@pytest.mark.skipif(sys.platform != "darwin", reason="macOS specific test")
def test_open(open_command, first_app_config, tmp_path):
    """On macOS, Open starts the finder on the Content folder."""
    # Create the binary that would be in the project bundle.
    create_file(
        open_command.project_path(first_app_config) / "MacOS" / "First App",
        "binary",
    )

    open_command(first_app_config)

    open_command.tools.subprocess.Popen.assert_called_once_with(
        [
            "open",
            tmp_path
            / "base_path"
            / "macOS"
            / "app"
            / "First App"
            / "First App.app"
            / "Contents",
        ]
    )
