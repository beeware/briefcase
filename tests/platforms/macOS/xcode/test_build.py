import subprocess
from unittest.mock import ANY, MagicMock

import pytest

from briefcase.console import Console, LogLevel
from briefcase.exceptions import BriefcaseCommandError
from briefcase.integrations.subprocess import Subprocess
from briefcase.platforms.macOS.xcode import macOSXcodeBuildCommand


@pytest.fixture
def build_command(tmp_path):
    command = macOSXcodeBuildCommand(
        console=Console(),
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )
    command.verify_not_on_icloud = MagicMock()

    return command


@pytest.mark.parametrize("tool_debug_mode", (True, False))
def test_build_app(build_command, first_app_generated, tool_debug_mode, tmp_path):
    """An macOS App can be built."""
    # Enable verbose tool logging
    if tool_debug_mode:
        build_command.tools.console.verbosity = LogLevel.DEEP_DEBUG

    build_command.tools.subprocess = MagicMock(spec_set=Subprocess)
    build_command.build_app(first_app_generated)

    # We verified we aren't on iCloud
    build_command.verify_not_on_icloud.assert_called_once_with(first_app_generated)

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
        build_command.build_app(first_app_generated)

    # We verified we aren't on iCloud
    build_command.verify_not_on_icloud.assert_called_once_with(first_app_generated)

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
