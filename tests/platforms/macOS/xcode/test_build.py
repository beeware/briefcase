import subprocess
from unittest.mock import ANY, MagicMock

import pytest

from briefcase.console import Console, Log, LogLevel
from briefcase.exceptions import BriefcaseCommandError
from briefcase.integrations.subprocess import Subprocess
from briefcase.platforms.macOS.xcode import macOSXcodeBuildCommand


@pytest.fixture
def build_command(tmp_path):
    return macOSXcodeBuildCommand(
        logger=Log(),
        console=Console(),
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )


@pytest.mark.parametrize("tool_debug_mode", (True, False))
def test_build_app(build_command, first_app_generated, tool_debug_mode, tmp_path):
    """An macOS App can be built."""
    # Enable verbose tool logging
    if tool_debug_mode:
        build_command.tools.logger.verbosity = LogLevel.DEEP_DEBUG

    build_command.tools.subprocess = MagicMock(spec_set=Subprocess)
    build_command.build_app(first_app_generated, test_mode=False)

    build_command.tools.subprocess.run.assert_called_with(
        [
            "xcodebuild",
            "-project",
            tmp_path
            / "base_path"
            / "build"
            / "first-app"
            / "macos"
            / "xcode"
            / "First App.xcodeproj",
            "-verbose" if tool_debug_mode else "-quiet",
            "-configuration",
            "Release",
            "build",
        ],
        check=True,
        filter_func=None if tool_debug_mode else ANY,
    )


def test_build_app_failed(build_command, first_app_generated, tmp_path):
    """If xcodebuild fails, an error is raised."""
    # The subprocess.run() call will raise an error
    build_command.tools.subprocess = MagicMock(spec_set=Subprocess)
    build_command.tools.subprocess.run.side_effect = subprocess.CalledProcessError(
        cmd=["xcodebuild", "..."],
        returncode=1,
    )

    with pytest.raises(BriefcaseCommandError):
        build_command.build_app(first_app_generated, test_mode=False)

    build_command.tools.subprocess.run.assert_called_with(
        [
            "xcodebuild",
            "-project",
            tmp_path
            / "base_path"
            / "build"
            / "first-app"
            / "macos"
            / "xcode"
            / "First App.xcodeproj",
            "-quiet",
            "-configuration",
            "Release",
            "build",
        ],
        check=True,
        filter_func=ANY,
    )
