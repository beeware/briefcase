# The run command inherits most of it's behavior from the common base
# implementation. Do a surface-level verification here, but the app
# tests provide the actual test coverage.
import os
from unittest import mock

from briefcase.platforms.windows.visualstudio import WindowsVisualStudioRunCommand


def test_run_app(first_app_config, tmp_path):
    """A windows Visual Studio project app can be started."""
    command = WindowsVisualStudioRunCommand(base_path=tmp_path)
    command.subprocess = mock.MagicMock()

    command.run_app(first_app_config)

    command.subprocess.run.assert_called_with(
        [
            os.fsdecode(
                tmp_path
                / "windows"
                / "VisualStudio"
                / "First App"
                / "x64"
                / "Release"
                / "First App.exe"
            ),
        ],
        cwd=tmp_path / "windows",
        check=True,
    )
