# The run command inherits most of its behavior from the common base
# implementation. Do a surface-level verification here, but the app
# tests provide the actual test coverage.
import os
from unittest import mock

from briefcase.console import Console, Log
from briefcase.integrations.subprocess import Subprocess
from briefcase.platforms.windows.visualstudio import WindowsVisualStudioRunCommand


def test_run_app(first_app_config, tmp_path):
    """A windows Visual Studio project app can be started."""
    command = WindowsVisualStudioRunCommand(
        logger=Log(),
        console=Console(),
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )
    command.tools.home_path = tmp_path / "home"
    command.tools.subprocess = mock.MagicMock(spec_set=Subprocess)

    command.run_app(first_app_config)

    command.tools.subprocess.run.assert_called_with(
        [
            os.fsdecode(
                tmp_path
                / "base_path"
                / "windows"
                / "VisualStudio"
                / "First App"
                / "x64"
                / "Release"
                / "First App.exe"
            ),
        ],
        cwd=tmp_path / "home",
        check=True,
        stream_output=True,
    )
