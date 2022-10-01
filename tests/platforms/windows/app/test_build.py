import subprocess
from pathlib import Path
from unittest import mock

import pytest

from briefcase.console import Console, Log
from briefcase.exceptions import BriefcaseCommandError
from briefcase.integrations.rcedit import RCEdit
from briefcase.integrations.subprocess import Subprocess
from briefcase.platforms.windows.app import WindowsAppBuildCommand


@pytest.fixture
def build_command(tmp_path):
    command = WindowsAppBuildCommand(
        logger=Log(),
        console=Console(),
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )
    command.tools.subprocess = mock.MagicMock(spec_set=Subprocess)
    command.tools.rcedit = RCEdit(command.tools)
    return command


def test_verify(build_command):
    """Verifying on Windows creates an RCEdit wrapper."""

    build_command.tools.subprocess = mock.MagicMock(spec_set=Subprocess)

    build_command.verify_tools()

    # No error, and an SDK wrapper is created
    assert isinstance(build_command.tools.rcedit, RCEdit)


def test_build_app(build_command, first_app_config, tmp_path):
    """The stub binary will be updated when a Windows app is built."""

    build_command.build_app(first_app_config)

    build_command.tools.subprocess.run.assert_has_calls(
        [
            # Collect manifest
            mock.call(
                [
                    tmp_path / "briefcase" / "tools" / "rcedit-x64.exe",
                    Path("src/First App.exe"),
                    "--set-version-string",
                    "CompanyName",
                    "Megacorp",
                    "--set-version-string",
                    "FileDescription",
                    "First App",
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
                    "ProductVersion",
                    "0.0.1",
                    "--set-icon",
                    "icon.ico",
                ],
                check=True,
                cwd=tmp_path / "base_path" / "windows" / "app" / "First App",
            ),
        ]
    )


def test_build_app_failure(build_command, first_app_config, tmp_path):
    """If the stub binary cannot be updated, an error is raised."""

    build_command.tools.subprocess.run.side_effect = subprocess.CalledProcessError(
        returncode=1,
        cmd="rcedit-x64.exe",
    )

    with pytest.raises(
        BriefcaseCommandError,
        match=r"Unable to update details on stub app for first-app.",
    ):
        build_command.build_app(first_app_config)
