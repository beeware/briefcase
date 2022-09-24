import subprocess
from unittest.mock import MagicMock

import pytest

from briefcase.console import Console, Log
from briefcase.exceptions import BriefcaseCommandError
from briefcase.integrations.subprocess import Subprocess
from briefcase.platforms.macOS.xcode import macOSXcodeBuildCommand


def test_build_app(first_app_config, tmp_path):
    """An macOS App can be built."""
    command = macOSXcodeBuildCommand(
        logger=Log(),
        console=Console(),
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )

    command.tools.subprocess = MagicMock(spec_set=Subprocess)
    command.build_app(first_app_config)

    command.tools.subprocess.run.assert_called_with(
        [
            "xcodebuild",
            "-project",
            tmp_path
            / "base_path"
            / "macOS"
            / "Xcode"
            / "First App"
            / "First App.xcodeproj",
            "-quiet",
            "-configuration",
            "Release",
            "build",
        ],
        check=True,
    )


def test_build_app_failed(first_app_config, tmp_path):
    """If xcodebuild fails, an error is raised."""
    command = macOSXcodeBuildCommand(
        logger=Log(),
        console=Console(),
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )

    # The subprocess.run() call will raise an error
    command.tools.subprocess = MagicMock(spec_set=Subprocess)
    command.tools.subprocess.run.side_effect = subprocess.CalledProcessError(
        cmd=["xcodebuild", "..."],
        returncode=1,
    )

    with pytest.raises(BriefcaseCommandError):
        command.build_app(first_app_config)

    command.tools.subprocess.run.assert_called_with(
        [
            "xcodebuild",
            "-project",
            tmp_path
            / "base_path"
            / "macOS"
            / "Xcode"
            / "First App"
            / "First App.xcodeproj",
            "-quiet",
            "-configuration",
            "Release",
            "build",
        ],
        check=True,
    )
