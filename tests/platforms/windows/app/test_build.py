from pathlib import Path
from unittest import mock

import pytest

from briefcase.integrations.rcedit import RCEdit
from briefcase.platforms.windows.app import WindowsAppBuildCommand


@pytest.fixture
def package_command(tmp_path):
    command = WindowsAppBuildCommand(base_path=tmp_path)
    command.tools_path = tmp_path / "tools"
    command.subprocess = mock.MagicMock()
    command.rcedit = RCEdit(command=command)
    return command


def test_build_app(package_command, first_app_config, tmp_path):
    """The stub binary will be updated when a Windows app is built."""

    package_command.build_app(first_app_config)

    package_command.subprocess.run.assert_has_calls(
        [
            # Collect manifest
            mock.call(
                [
                    tmp_path / "tools" / "rcedit-x64.exe",
                    Path("src/First App.exe"),
                    "--set-version-string",
                    "CompanyName",
                    "Megacorp",
                    "--set-version-string",
                    "FileDescription",
                    "The first simple app",
                    "--set-version-string",
                    "FileVersion",
                    "0.0.1",
                    "--set-version-string",
                    "InternalName",
                    "first_app",
                    "--set-version-string",
                    "OriginalFilename",
                    "First App.exe",
                    "--set-version-string",
                    "ProductName",
                    "First App",
                    "--set-version-string",
                    "productVersion",
                    "0.0.1",
                    "--set-icon",
                    "icon.ico",
                ],
                check=True,
                cwd=tmp_path / "windows" / "app" / "First App",
            ),
        ]
    )
