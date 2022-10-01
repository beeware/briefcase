import subprocess
from pathlib import Path
from unittest import mock

import pytest

from briefcase.console import Console, Log
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
        msbuild_path=tmp_path / "Visual Studio" / "MSBuild.exe",
    )
    return command


def test_verify(build_command):
    """Verifying on Windows creates a VisualStudio wrapper."""

    build_command.tools.subprocess = mock.MagicMock(spec_set=Subprocess)

    build_command.verify_tools()

    # No error, and an SDK wrapper is created
    assert isinstance(build_command.tools.visualstudio, VisualStudio)


def test_build_app(build_command, first_app_config, tmp_path):
    """The solution will be compiled when the project is built."""

    build_command.build_app(first_app_config)

    build_command.tools.subprocess.run.assert_has_calls(
        [
            # Collect manifest
            mock.call(
                [
                    Path(tmp_path) / "Visual Studio" / "MSBuild.exe",
                    "First App.sln",
                    "-target:restore",
                    "-property:RestorePackagesConfig=true",
                    "-target:First App",
                    "-property:Configuration=Release",
                ],
                check=True,
                cwd=tmp_path / "base_path" / "windows" / "VisualStudio" / "First App",
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
