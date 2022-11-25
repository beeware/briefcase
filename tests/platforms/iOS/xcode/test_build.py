import plistlib
import subprocess
from unittest import mock

import pytest

from briefcase.console import Console, Log
from briefcase.exceptions import BriefcaseCommandError
from briefcase.integrations.subprocess import Subprocess
from briefcase.platforms.iOS.xcode import iOSXcodeBuildCommand


@pytest.fixture
def build_command(tmp_path):
    return iOSXcodeBuildCommand(
        logger=Log(),
        console=Console(),
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )


def test_build_app(build_command, first_app_generated, tmp_path):
    """An iOS App can be built."""
    build_command.tools.subprocess = mock.MagicMock(spec_set=Subprocess)

    # Mock the host's CPU architecture to ensure it's reflected in the Xcode call
    build_command.tools.host_arch = "weird"

    build_command.build_app(first_app_generated)

    build_command.tools.subprocess.run.assert_called_with(
        [
            "xcodebuild",
            "build",
            "-project",
            tmp_path
            / "base_path"
            / "iOS"
            / "Xcode"
            / "First App"
            / "First App.xcodeproj",
            "-destination",
            'platform="iOS Simulator"',
            "-configuration",
            "Debug",
            "-arch",
            "weird",
            "-sdk",
            "iphonesimulator",
            "-quiet",
        ],
        check=True,
    )

    # The app metadata references the app module
    with (tmp_path / "base_path" / "iOS" / "Xcode" / "First App" / "Info.plist").open(
        "rb"
    ) as f:
        plist = plistlib.load(f)
        assert plist["MainModule"] == "first_app"


def test_build_app_test_mode(build_command, first_app_generated, tmp_path):
    """An iOS App can be built in test mode."""
    build_command.tools.subprocess = mock.MagicMock(spec_set=Subprocess)

    # Mock the host's CPU architecture to ensure it's reflected in the Xcode call
    build_command.tools.host_arch = "weird"

    build_command.build_app(first_app_generated, test_mode=True)

    build_command.tools.subprocess.run.assert_called_with(
        [
            "xcodebuild",
            "build",
            "-project",
            tmp_path
            / "base_path"
            / "iOS"
            / "Xcode"
            / "First App"
            / "First App.xcodeproj",
            "-destination",
            'platform="iOS Simulator"',
            "-configuration",
            "Debug",
            "-arch",
            "weird",
            "-sdk",
            "iphonesimulator",
            "-quiet",
        ],
        check=True,
    )

    # The app metadata has been rewritten to reference the test module
    with (tmp_path / "base_path" / "iOS" / "Xcode" / "First App" / "Info.plist").open(
        "rb"
    ) as f:
        plist = plistlib.load(f)
        assert plist["MainModule"] == "tests.first_app"


def test_build_app_failed(build_command, first_app_generated, tmp_path):
    """If xcodebuild fails, an error is raised."""
    # The subprocess.run() call will raise an error
    build_command.tools.subprocess = mock.MagicMock(spec_set=Subprocess)
    build_command.tools.subprocess.run.side_effect = subprocess.CalledProcessError(
        cmd=["xcodebuild", "..."], returncode=1
    )

    # Mock the host's CPU architecture to ensure it's reflected in the Xcode call
    build_command.tools.host_arch = "weird"

    with pytest.raises(BriefcaseCommandError):
        build_command.build_app(first_app_generated)

    build_command.tools.subprocess.run.assert_called_with(
        [
            "xcodebuild",
            "build",
            "-project",
            tmp_path
            / "base_path"
            / "iOS"
            / "Xcode"
            / "First App"
            / "First App.xcodeproj",
            "-destination",
            'platform="iOS Simulator"',
            "-configuration",
            "Debug",
            "-arch",
            "weird",
            "-sdk",
            "iphonesimulator",
            "-quiet",
        ],
        check=True,
    )
