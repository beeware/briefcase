import subprocess
from pathlib import Path
from unittest import mock

import pytest

from briefcase.exceptions import BriefcaseCommandError
from briefcase.integrations.visualstudio import VisualStudio
from briefcase.platforms.windows.visualstudio import WindowsVisualStudioBuildCommand


@pytest.fixture
def package_command(tmp_path):
    command = WindowsVisualStudioBuildCommand(base_path=tmp_path)
    command.tools_path = tmp_path / "tools"
    command.subprocess = mock.MagicMock()
    command.visualstudio = VisualStudio(
        command=command,
        msbuild_path=tmp_path / "Visual Studio" / "MSBuild.exe",
    )
    return command


def test_build_app(package_command, first_app_config, tmp_path):
    """The solution will be compiled when the project is built."""

    package_command.build_app(first_app_config)

    package_command.subprocess.run.assert_has_calls(
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
                cwd=tmp_path / "windows" / "VisualStudio" / "First App",
            ),
        ]
    )


def test_build_app_failure(package_command, first_app_config, tmp_path):
    """If the stub binary cannot be updated, an error is raised."""

    package_command.subprocess.run.side_effect = subprocess.CalledProcessError(
        returncode=1,
        cmd="MSBuild.exe",
    )

    with pytest.raises(
        BriefcaseCommandError,
        match=r"Unable to build solution for first-app.",
    ):
        package_command.build_app(first_app_config)
