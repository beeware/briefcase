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


def test_device_option(build_command):
    """The -d option can be parsed."""
    options = build_command.parse_options(["-d", "myphone"])

    assert options == {"udid": "myphone", "update": False}


def test_build_app(build_command, first_app_config, tmp_path):
    """An iOS App can be built."""
    # A valid target device will be selected.
    build_command.select_target_device = mock.MagicMock(
        return_value=("2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D", "13.2", "iPhone 11")
    )
    build_command.tools.subprocess = mock.MagicMock(spec_set=Subprocess)

    # Mock the host's CPU architecture to ensure it's reflected in the Xcode call
    build_command.tools.host_arch = "weird"

    build_command.build_app(first_app_config)

    build_command.tools.subprocess.run.assert_called_with(
        [
            "xcodebuild",
            "-project",
            tmp_path
            / "base_path"
            / "iOS"
            / "Xcode"
            / "First App"
            / "First App.xcodeproj",
            "-destination",
            'platform="iOS Simulator,name=iPhone 11,OS=13.2"',
            "-quiet",
            "-configuration",
            "Debug",
            "-arch",
            "weird",
            "-sdk",
            "iphonesimulator",
            "build",
        ],
        check=True,
    )


def test_build_multiple_devices_input_disabled(build_command, first_app_config):
    """If input is disabled, but there are multiple devices, an error is
    raised."""
    # Multiple devices are available
    build_command.get_simulators = mock.MagicMock(
        return_value={
            "iOS 13.2": {
                "C9A005C8-9468-47C5-8376-68A6E3408209": "iPhone 8",
                "2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D": "iPhone 11",
                "EEEBA06C-81F9-407C-885A-2261306DB2BE": "iPhone 11 Pro Max",
            }
        }
    )

    # Disable console input.
    build_command.tools.input.enabled = False

    with pytest.raises(
        BriefcaseCommandError,
        match=r"Input has been disabled; can't select a device to target.",
    ):
        build_command.build_app(first_app_config)


def test_build_app_failed(build_command, first_app_config, tmp_path):
    """If xcodebuild fails, an error is raised."""
    # A valid target device will be selected.
    build_command.select_target_device = mock.MagicMock(
        return_value=("2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D", "13.2", "iPhone 11")
    )
    # The subprocess.run() call will raise an error
    build_command.tools.subprocess = mock.MagicMock(spec_set=Subprocess)
    build_command.tools.subprocess.run.side_effect = subprocess.CalledProcessError(
        cmd=["xcodebuild", "..."], returncode=1
    )

    # Mock the host's CPU architecture to ensure it's reflected in the Xcode call
    build_command.tools.host_arch = "weird"

    with pytest.raises(BriefcaseCommandError):
        build_command.build_app(first_app_config)

    build_command.tools.subprocess.run.assert_called_with(
        [
            "xcodebuild",
            "-project",
            tmp_path
            / "base_path"
            / "iOS"
            / "Xcode"
            / "First App"
            / "First App.xcodeproj",
            "-destination",
            'platform="iOS Simulator,name=iPhone 11,OS=13.2"',
            "-quiet",
            "-configuration",
            "Debug",
            "-arch",
            "weird",
            "-sdk",
            "iphonesimulator",
            "build",
        ],
        check=True,
    )
