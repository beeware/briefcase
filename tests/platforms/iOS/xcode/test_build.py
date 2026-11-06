import plistlib
import subprocess
from unittest import mock

import pytest

from briefcase.console import LogLevel
from briefcase.exceptions import BriefcaseCommandError
from briefcase.integrations.subprocess import Subprocess
from briefcase.platforms.iOS.xcode import (
    iOSDevice,
    iOSSigningIdentity,
    iOSXcodeBuildCommand,
)


@pytest.fixture
def build_command(dummy_console, tmp_path):
    return iOSXcodeBuildCommand(
        console=dummy_console,
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )


def test_device_options(build_command):
    """The -d and -i options can be parsed; by default, no device is selected."""
    options, _ = build_command.parse_options(
        ["-d", "Test iPhone", "-i", "Apple Development: jane@example.com (MEMBER1234)"]
    )
    assert options["udid"] == "Test iPhone"
    assert options["identity"] == "Apple Development: jane@example.com (MEMBER1234)"

    options, _ = build_command.parse_options([])
    assert "udid" not in options
    assert options["identity"] is None


@pytest.mark.parametrize("preselected", [True, False])
def test_build_app_physical_device(
    build_command,
    first_app_generated,
    preselected,
    tmp_path,
):
    """An iOS App can be built for a physical device, signed by the identity's team."""
    build_command.tools.subprocess = mock.MagicMock(spec_set=Subprocess)

    device = iOSDevice(
        "00008110-001122334455667E",
        "26.0.1",
        "Test iPhone",
        physical=True,
    )
    identity = iOSSigningIdentity(
        id="22222222222222222222222222222222222222BB",
        name="Apple Development: jane@example.com (MEMBER1234)",
        team_id="TEAM123456",
    )
    build_command.select_target_device = mock.MagicMock(return_value=device)
    build_command.select_identity = mock.MagicMock(return_value=identity)

    if preselected:
        # The device and identity were selected by the run command.
        build_command.target_device = device
        build_command.signing_identity = identity
        build_command.build_app(first_app_generated, udid="Test iPhone")
        build_command.select_target_device.assert_not_called()
    else:
        build_command.build_app(
            first_app_generated,
            udid="Test iPhone",
            identity=None,
        )
        build_command.select_target_device.assert_called_once_with("Test iPhone")
        build_command.select_identity.assert_called_once_with(None)

    build_command.tools.subprocess.run.assert_called_with(
        [
            "xcodebuild",
            "build",
            "-project",
            tmp_path
            / "base_path"
            / "build"
            / "first-app"
            / "ios"
            / "xcode"
            / "First App.xcodeproj",
            "-configuration",
            "Debug",
            "-scheme",
            "First App",
            "-destination",
            "id=00008110-001122334455667E",
            "-allowProvisioningUpdates",
            "-allowProvisioningDeviceRegistration",
            "DEVELOPMENT_TEAM=TEAM123456",
            f"SYMROOT={tmp_path / 'base_path/build/first-app/ios/xcode/build'}",
            "-quiet",
        ],
        check=True,
        filter_func=mock.ANY,
    )


@pytest.mark.parametrize("tool_debug_mode", [True, False])
def test_build_app(build_command, first_app_generated, tool_debug_mode, tmp_path):
    """An iOS App can be built."""
    build_command.tools.subprocess = mock.MagicMock(spec_set=Subprocess)

    # Mock the host's CPU architecture to ensure it's reflected in the Xcode call
    build_command.tools.host_arch = "weird"

    # Enable verbose tool logging
    if tool_debug_mode:
        build_command.tools.console.verbosity = LogLevel.DEEP_DEBUG

    build_command.build_app(first_app_generated)

    build_command.tools.subprocess.run.assert_called_with(
        [
            "xcodebuild",
            "build",
            "-project",
            tmp_path
            / "base_path"
            / "build"
            / "first-app"
            / "ios"
            / "xcode"
            / "First App.xcodeproj",
            "-configuration",
            "Debug",
            "-arch",
            "weird",
            "-sdk",
            "iphonesimulator",
            "-verbose" if tool_debug_mode else "-quiet",
        ],
        check=True,
        filter_func=None if tool_debug_mode else mock.ANY,
    )

    # The app metadata references the app module
    with (tmp_path / "base_path/build/first-app/ios/xcode/Info.plist").open("rb") as f:
        plist = plistlib.load(f)
        assert plist["MainModule"] == "first_app"


def test_build_app_test_mode(build_command, first_app_generated, tmp_path):
    """An iOS App can be built in test mode."""
    first_app_generated.test_mode = True

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
            / "build"
            / "first-app"
            / "ios"
            / "xcode"
            / "First App.xcodeproj",
            "-configuration",
            "Debug",
            "-arch",
            "weird",
            "-sdk",
            "iphonesimulator",
            "-quiet",
        ],
        check=True,
        filter_func=mock.ANY,
    )

    # The app metadata has been rewritten to reference the test module
    with (tmp_path / "base_path/build/first-app/ios/xcode/Info.plist").open("rb") as f:
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
            / "build"
            / "first-app"
            / "ios"
            / "xcode"
            / "First App.xcodeproj",
            "-configuration",
            "Debug",
            "-arch",
            "weird",
            "-sdk",
            "iphonesimulator",
            "-quiet",
        ],
        check=True,
        filter_func=mock.ANY,
    )
