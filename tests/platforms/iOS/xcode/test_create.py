import shutil
import sys
from unittest import mock

import pytest

from briefcase.exceptions import (
    BriefcaseCommandError,
    UnsupportedHostError,
)
from briefcase.platforms.iOS.xcode import iOSXcodeCreateCommand

from ....utils import create_file, create_plist_file


@pytest.fixture
def create_command(dummy_console, tmp_path):
    command = iOSXcodeCreateCommand(
        console=dummy_console,
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )

    command.tools.sys = mock.MagicMock(spec_set=sys)
    command.tools.sys.version_info = (3, "X", 0)

    return command


@pytest.mark.parametrize("host_os", ["Linux", "Windows", "WeirdOS"])
def test_unsupported_host_os(create_command, host_os):
    """Error raised for an unsupported OS."""
    create_command.tools.host_os = host_os

    with pytest.raises(
        UnsupportedHostError,
        match=r"iOS applications require Xcode, which is only available on macOS\.",
    ):
        create_command()


@pytest.mark.parametrize(
    ("platform", "arch", "venv_platform", "platform_path"),
    [
        (
            "iOS",
            "arm64",
            "iphoneos",
            "Python.xcframework/ios-arm64/platform-config/arm64-iphoneos",
        ),
        (
            "iphonesimulator",
            "arm64",
            "iphonesimulator",
            "Python.xcframework/ios-arm64_x86_64-simulator/platform-config/arm64-iphonesimulator",
        ),
        (
            "iphonesimulator",
            "x86_64",
            "iphonesimulator",
            "Python.xcframework/ios-arm64_x86_64-simulator/platform-config/x86_64-iphonesimulator",
        ),
    ],
)
def test_create_app_environment(
    create_command,
    first_app_generated,
    tmp_path,
    platform,
    arch,
    venv_platform,
    platform_path,
):
    """An iOS app can create cross-environments with a platform path."""
    create_command.tools.subprocess = mock.MagicMock()
    create_command.tools[
        first_app_generated
    ].app_context = create_command.tools.subprocess

    venv = create_command.create_app_environment(
        first_app_generated,
        platform,
        arch,
        "venv",
    )

    assert venv.platform == venv_platform
    assert venv.arch == arch
    assert venv.name == f"{venv_platform}-{arch}"
    assert (
        venv.platform_path
        == tmp_path / "base_path/build/first-app/ios/xcode/Support" / platform_path
    )


def test_install_requirements(
    create_command,
    mock_venv,
    mock_sim_venv,
    first_app_generated,
    tmp_path,
):
    """Extra iOS-specific args are included in calls to pip during update."""
    # Hard code the current architecture for testing. We only install simulator
    # requirements for the current platform.
    create_command.tools.host_arch = "wonky"
    create_command.create_app_environment = mock.MagicMock(return_value=mock_sim_venv)

    first_app_generated.requires = ["something==1.2.3", "other>=2.3.4"]

    create_command.install_app_requirements(first_app_generated, mock_venv)

    bundle_path = tmp_path / "base_path/build/first-app/ios/xcode"
    mock_venv.install_requirements.assert_called_once_with(
        [
            "something==1.2.3",
            "other>=2.3.4",
        ],
        allow_editable=False,
        require_binary=True,
        min_os_version="12.0",
        install_path=bundle_path / "app_packages.iphoneos",
        install_hint=(
            "\n\n"
            "This may be because the `iphoneos` wheels that are available are not compatible\n"
            "with Python 3.X and a minimum iOS version of 12.0.\n"
        ),
    )
    mock_sim_venv.install_requirements.assert_called_once_with(
        [
            "something==1.2.3",
            "other>=2.3.4",
        ],
        allow_editable=False,
        require_binary=True,
        min_os_version="12.0",
        install_path=bundle_path / "app_packages.iphonesimulator",
        install_hint=(
            "\n\n"
            "This may indicate that an `iphoneos` wheel could be found, but an\n"
            "`iphonesimulator` wheel could not be found; or that the `iphonesimulator`\n"
            "binary wheels that are available are not compatible with\n"
            "Python 3.X and a minimum iOS version of 12.0.\n"
        ),
    )


@pytest.mark.parametrize("include_version", [True, False])
def test_legacy_support_format(
    create_command,
    mock_venv,
    mock_sim_venv,
    first_app_generated,
    include_version,
    tmp_path,
):
    """A support package is in the legacy format is still supported."""
    # Remove the version tag from the framework if the test requires
    if include_version:
        version = "12.0"
    else:
        version = "13.0"

    # If we're testing an old config, delete the xcframework. This deletes the platform
    # config folders, forcing a fallback to the older locations.
    shutil.rmtree(
        tmp_path / "base_path/build/first-app/ios/xcode/Support/Python.xcframework"
    )
    # Create the old-style VERSIONS file.
    create_file(
        tmp_path / "base_path/build/first-app/ios/xcode/Support/VERSIONS",
        "\n".join(
            [
                "Python version: 3.10.15",
                "Build: b11",
                ("Min iOS version: 12.0" if include_version else ""),
                "---------------------",
                "BZip2: 1.0.8-1",
                "libFFI: 3.4.6-1",
                "OpenSSL: 3.0.15-1",
                "XZ: 5.6.2-1",
                "",
            ]
        ),
    )

    # Hard code the current architecture for testing. We only install simulator
    # requirements for the current platform.
    create_command.tools.host_arch = "wonky"
    create_command.create_app_environment = mock.MagicMock(return_value=mock_sim_venv)

    first_app_generated.requires = ["something==1.2.3", "other>=2.3.4"]

    create_command.install_app_requirements(first_app_generated, mock_venv)

    bundle_path = tmp_path / "base_path/build/first-app/ios/xcode"
    mock_venv.install_requirements.assert_called_once_with(
        [
            "something==1.2.3",
            "other>=2.3.4",
        ],
        allow_editable=False,
        require_binary=True,
        min_os_version=version,
        install_path=bundle_path / "app_packages.iphoneos",
        install_hint=mock.ANY,
    )
    mock_sim_venv.install_requirements.assert_called_once_with(
        [
            "something==1.2.3",
            "other>=2.3.4",
        ],
        allow_editable=False,
        require_binary=True,
        min_os_version=version,
        install_path=bundle_path / "app_packages.iphonesimulator",
        install_hint=mock.ANY,
    )


def test_min_os_version(
    create_command,
    mock_venv,
    mock_sim_venv,
    first_app_generated,
    tmp_path,
):
    """If a minimum iOS version is specified, it is used for wheel installs."""

    # Hard code the current architecture for testing. We only install simulator
    # requirements for the current platform.
    create_command.tools.host_arch = "wonky"
    create_command.create_app_environment = mock.MagicMock(return_value=mock_sim_venv)

    first_app_generated.requires = ["something==1.2.3", "other>=2.3.4"]

    # Set a minimum OS version
    first_app_generated.min_os_version = "15.2"

    create_command.install_app_requirements(first_app_generated, mock_venv)

    bundle_path = tmp_path / "base_path/build/first-app/ios/xcode"
    mock_venv.install_requirements.assert_called_once_with(
        [
            "something==1.2.3",
            "other>=2.3.4",
        ],
        allow_editable=False,
        require_binary=True,
        min_os_version="15.2",
        install_path=bundle_path / "app_packages.iphoneos",
        install_hint=mock.ANY,
    )
    mock_sim_venv.install_requirements.assert_called_once_with(
        [
            "something==1.2.3",
            "other>=2.3.4",
        ],
        allow_editable=False,
        require_binary=True,
        min_os_version="15.2",
        install_path=bundle_path / "app_packages.iphonesimulator",
        install_hint=mock.ANY,
    )


def test_framework_missing_min_version(
    create_command,
    mock_venv,
    mock_sim_venv,
    first_app_generated,
    tmp_path,
):
    """If the iOS framework is missing a minimum version definition, raise an error."""
    # Replace the XCframework Info.plist file with a version that doesn't specify
    # a minimum iOS version.
    plist_file = (
        tmp_path
        / "base_path/build/first-app/ios/xcode/Support/Python.xcframework"
        / "ios-arm64/Python.framework/Info.plist"
    )
    plist_file.unlink()
    create_plist_file(
        plist_file,
        {
            "CFBundleSupportedPlatforms": "iPhoneOS",
            "CFBundleVersion": "3.10.15",
        },
    )

    # Hard code the current architecture for testing. We only install simulator
    # requirements for the current platform.
    create_command.tools.host_arch = "wonky"
    create_command.create_app_environment = mock.MagicMock(return_value=mock_sim_venv)

    first_app_generated.requires = ["something==1.2.3", "other>=2.3.4"]

    with pytest.raises(
        BriefcaseCommandError,
        match=r"Your iOS XCframework doesn't specify a minimum iOS version",
    ):
        create_command.install_app_requirements(first_app_generated, mock_venv)

    # No attempt to install requirements was made
    mock_venv.install_requirements.assert_not_called()
    mock_sim_venv.install_requirements.assert_not_called()


def test_incompatible_min_os_version(
    create_command,
    mock_venv,
    mock_sim_venv,
    first_app_generated,
    tmp_path,
):
    """If the app's iOS version isn't compatible with the support package, an error is
    raised."""
    # Hard code the current architecture for testing. We only install simulator
    # requirements for the current platform.
    create_command.tools.host_arch = "wonky"
    create_command.create_app_environment = mock.MagicMock(return_value=mock_sim_venv)

    first_app_generated.requires = ["something==1.2.3", "other>=2.3.4"]
    first_app_generated.min_os_version = "8.0"

    with pytest.raises(
        BriefcaseCommandError,
        match=(
            r"Your iOS app specifies a minimum iOS version of 8.0, "
            r"but the support package only supports 12.0"
        ),
    ):
        create_command.install_app_requirements(first_app_generated, mock_venv)

    # No attempt to install requirements was made
    mock_venv.install_requirements.assert_not_called()
    mock_sim_venv.install_requirements.assert_not_called()


@pytest.mark.parametrize(
    ("permissions", "info", "context"),
    [
        # No permissions
        (
            {},
            {},
            {"info": {}},
        ),
        # Only custom permissions
        (
            {},
            {
                "NSCameraUsageDescription": "I need to see you",
                "NSMicrophoneUsageDescription": "I need to hear you",
            },
            {
                "info": {
                    "NSCameraUsageDescription": "I need to see you",
                    "NSMicrophoneUsageDescription": "I need to hear you",
                }
            },
        ),
        # Bluetooth permissions
        (
            {
                "bluetooth": "I need to connect to bluetooth device.",
            },
            {},
            {
                "info": {
                    "NSBluetoothAlwaysUsageDescription": "I need to connect to bluetooth device."
                },
            },
        ),
        # Camera permissions
        (
            {
                "camera": "I need to see you",
            },
            {},
            {
                "info": {
                    "NSCameraUsageDescription": "I need to see you",
                },
            },
        ),
        # Microphone permissions
        (
            {
                "microphone": "I need to hear you",
            },
            {},
            {
                "info": {
                    "NSMicrophoneUsageDescription": "I need to hear you",
                },
            },
        ),
        # Coarse location permissions
        (
            {
                "coarse_location": "I need to know roughly where you are",
            },
            {},
            {
                "info": {
                    "NSLocationDefaultAccuracyReduced": True,
                    "NSLocationWhenInUseUsageDescription": "I need to know roughly where you are",
                }
            },
        ),
        # Fine location permissions
        (
            {
                "fine_location": "I need to know exactly where you are",
            },
            {},
            {
                "info": {
                    "NSLocationDefaultAccuracyReduced": False,
                    "NSLocationWhenInUseUsageDescription": "I need to know exactly where you are",
                }
            },
        ),
        # Background location permissions
        (
            {
                "background_location": "I always need to know where you are",
            },
            {},
            {
                "info": {
                    "NSLocationWhenInUseUsageDescription": "I always need to know where you are",
                    "NSLocationAlwaysAndWhenInUseUsageDescription": "I always need to know where you are",
                    "UIBackgroundModes": ["processing", "location"],
                }
            },
        ),
        # Coarse location background permissions
        (
            {
                "coarse_location": "I need to know roughly where you are",
                "background_location": "I always need to know where you are",
            },
            {},
            {
                "info": {
                    "NSLocationDefaultAccuracyReduced": True,
                    "NSLocationWhenInUseUsageDescription": "I need to know roughly where you are",
                    "NSLocationAlwaysAndWhenInUseUsageDescription": "I always need to know where you are",
                    "UIBackgroundModes": ["processing", "location"],
                }
            },
        ),
        # Fine location background permissions
        (
            {
                "fine_location": "I need to know exactly where you are",
                "background_location": "I always need to know where you are",
            },
            {},
            {
                "info": {
                    "NSLocationDefaultAccuracyReduced": False,
                    "NSLocationWhenInUseUsageDescription": "I need to know exactly where you are",
                    "NSLocationAlwaysAndWhenInUseUsageDescription": "I always need to know where you are",
                    "UIBackgroundModes": ["processing", "location"],
                }
            },
        ),
        # Coarse and fine location permissions
        (
            {
                "coarse_location": "I need to know roughly where you are",
                "fine_location": "I need to know exactly where you are",
            },
            {},
            {
                "info": {
                    "NSLocationDefaultAccuracyReduced": False,
                    "NSLocationWhenInUseUsageDescription": "I need to know exactly where you are",
                }
            },
        ),
        # Coarse and fine background location permissions
        (
            {
                "coarse_location": "I need to know roughly where you are",
                "fine_location": "I need to know exactly where you are",
                "background_location": "I always need to know where you are",
            },
            {},
            {
                "info": {
                    "NSLocationDefaultAccuracyReduced": False,
                    "NSLocationWhenInUseUsageDescription": "I need to know exactly where you are",
                    "NSLocationAlwaysAndWhenInUseUsageDescription": "I always need to know where you are",
                    "UIBackgroundModes": ["processing", "location"],
                }
            },
        ),
        # Photo library permissions
        (
            {
                "photo_library": "I need to see your library",
            },
            {},
            {
                "info": {
                    "NSPhotoLibraryAddUsageDescription": "I need to see your library"
                }
            },
        ),
        # Override and augment by cross-platform definitions
        (
            {
                "camera": "I need to see you",
            },
            {
                "NSCameraUsageDescription": "Platform specific",
                "NSCustomPermission": "Custom message",
            },
            {
                "info": {
                    "NSCameraUsageDescription": "Platform specific",
                    "NSCustomPermission": "Custom message",
                }
            },
        ),
    ],
)
def test_permissions_context(create_command, first_app, permissions, info, context):
    """Platform-specific permissions can be added to the context."""
    # Set the permissions value
    first_app.permission = permissions
    first_app.info = info
    # Extract the cross-platform permissions
    x_permissions = create_command._x_permissions(first_app)
    # Check that the final platform permissions are rendered as expected.
    assert context == create_command.permissions_context(first_app, x_permissions)
