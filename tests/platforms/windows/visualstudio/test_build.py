import subprocess
from pathlib import Path
from unittest import mock

import pytest

import briefcase.platforms.windows.visualstudio
from briefcase.console import Console, Log, LogLevel
from briefcase.exceptions import BriefcaseCommandError
from briefcase.integrations.subprocess import Subprocess
from briefcase.integrations.visualstudio import VisualStudio
from briefcase.platforms.windows.visualstudio import WindowsVisualStudioBuildCommand


@pytest.fixture
def build_command(tmp_path):
    command = WindowsVisualStudioBuildCommand(
        logger=Log(),
        console=Console(),
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )
    command.tools.subprocess = mock.MagicMock(spec_set=Subprocess)
    command.tools.visualstudio = VisualStudio(
        tools=command.tools,
        msbuild_path=tmp_path / "Visual Studio/MSBuild.exe",
    )
    return command


def test_verify(build_command, monkeypatch):
    """Verifying on Windows creates a VisualStudio wrapper."""
    build_command.tools.host_os = "Windows"

    mock_visualstudio_verify = mock.MagicMock(wraps=VisualStudio.verify)
    monkeypatch.setattr(
        briefcase.platforms.windows.visualstudio.VisualStudio,
        "verify",
        mock_visualstudio_verify,
    )

    build_command.verify_tools()

    # VisualStudio tool was verified
    mock_visualstudio_verify.assert_called_once_with(tools=build_command.tools)
    assert isinstance(build_command.tools.visualstudio, VisualStudio)


@pytest.mark.parametrize("tool_debug_mode", (True, False))
def test_build_app(build_command, first_app_config, tool_debug_mode, tmp_path):
    """The solution will be compiled when the project is built."""
    # Enable verbose tool logging
    if tool_debug_mode:
        build_command.tools.logger.verbosity = LogLevel.DEEP_DEBUG

    build_command.build_app(first_app_config)

    build_command.tools.subprocess.run.assert_has_calls(
        [
            # Collect manifest
            mock.call(
                [
                    Path(tmp_path) / "Visual Studio/MSBuild.exe",
                    "First App.sln",
                    "-target:restore",
                    "-property:RestorePackagesConfig=true",
                    "-target:First App",
                    "-property:Configuration=Release",
                    "-verbosity:detailed" if tool_debug_mode else "-verbosity:normal",
                ],
                check=True,
                cwd=tmp_path
                / "base_path"
                / "build"
                / "first-app"
                / "windows"
                / "visualstudio",
            ),
        ]
    )


def test_build_app_failure(build_command, first_app_config, tmp_path):
    """If the stub binary cannot be updated, an error is raised."""

    build_command.tools.subprocess.run.side_effect = subprocess.CalledProcessError(
        returncode=1,
        cmd="MSBuild.exe",
    )

    with pytest.raises(
        BriefcaseCommandError,
        match=r"Unable to build solution for first-app.",
    ):
        build_command.build_app(first_app_config)
