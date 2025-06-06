import shutil
import sys
from pathlib import Path
from subprocess import CalledProcessError
from unittest.mock import MagicMock, call

import pytest

from briefcase.console import Console
from briefcase.exceptions import (
    BriefcaseCommandError,
    RequirementsInstallError,
    UnsupportedHostError,
)
from briefcase.integrations.subprocess import Subprocess
from briefcase.platforms.iOS.xcode import iOSXcodeCreateCommand


@pytest.fixture
def create_command(tmp_path):
    return iOSXcodeCreateCommand(
        console=Console(),
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )


@pytest.mark.parametrize("host_os", ["Linux", "Windows", "WeirdOS"])
def test_unsupported_host_os(create_command, host_os):
    """Error raised for an unsupported OS."""
    create_command.tools.host_os = host_os

    with pytest.raises(
        UnsupportedHostError,
        match="iOS applications require Xcode, which is only available on macOS.",
    ):
        create_command()


@pytest.mark.parametrize(
    "old_config, device_config_path, sim_config_path",
    [
        (
            False,
            "Python.xcframework/ios-arm64/platform-config/arm64-iphoneos",
            "Python.xcframework/ios-arm64_x86_64-simulator/platform-config/wonky-iphonesimulator",
        ),
        (
            True,
            "platform-site/iphoneos.arm64",
            "platform-site/iphonesimulator.wonky",
        ),
    ],
)
def test_extra_pip_args(
    create_command,
    first_app_generated,
    old_config,
    device_config_path,
    sim_config_path,
    tmp_path,
):
    """Extra iOS-specific args are included in calls to pip during update."""
    # If we're testing an old config, delete the xcframework. This deletes the platform
    # config folders, forcing a fallback to the older locations.
    if old_config:
        shutil.rmtree(
            tmp_path / "base_path/build/first-app/ios/xcode/Support/Python.xcframework"
        )

    # Hard code the current architecture for testing. We only install simulator
    # requirements for the current platform.
    create_command.tools.host_arch = "wonky"

    first_app_generated.requires = ["something==1.2.3", "other>=2.3.4"]

    create_command.tools[first_app_generated].app_context = MagicMock(
        spec_set=Subprocess
    )

    create_command.install_app_requirements(first_app_generated)

    bundle_path = tmp_path / "base_path/build/first-app/ios/xcode"
    assert create_command.tools[first_app_generated].app_context.run.mock_calls == [
        call(
            [
                sys.executable,
                "-u",
                "-X",
                "utf8",
                "-m",
                "pip",
                "install",
                "--disable-pip-version-check",
                "--upgrade",
                "--no-user",
                f"--target={bundle_path / 'app_packages.iphoneos'}",
                "--only-binary=:all:",
                "--extra-index-url",
                "https://pypi.anaconda.org/beeware/simple",
                "--platform=ios_13_0_arm64_iphoneos",
                "something==1.2.3",
                "other>=2.3.4",
            ],
            check=True,
            encoding="UTF-8",
            env={
                "PYTHONPATH": str(
                    tmp_path
                    / "base_path/build/first-app/ios/xcode/Support"
                    / device_config_path
                ),
                "PIP_REQUIRE_VIRTUALENV": None,
            },
        ),
        call(
            [
                sys.executable,
                "-u",
                "-X",
                "utf8",
                "-m",
                "pip",
                "install",
                "--disable-pip-version-check",
                "--upgrade",
                "--no-user",
                f"--target={bundle_path / 'app_packages.iphonesimulator'}",
                "--only-binary=:all:",
                "--extra-index-url",
                "https://pypi.anaconda.org/beeware/simple",
                "--platform=ios_13_0_wonky_iphonesimulator",
                "something==1.2.3",
                "other>=2.3.4",
            ],
            check=True,
            encoding="UTF-8",
            env={
                "PYTHONPATH": str(
                    tmp_path
                    / "base_path/build/first-app/ios/xcode/Support"
                    / sim_config_path
                ),
                "PIP_REQUIRE_VIRTUALENV": None,
            },
        ),
    ]


def test_min_os_version(create_command, first_app_generated, tmp_path):
    """If a minimum iOS version is specified, it is used for wheel installs."""

    # Hard code the current architecture for testing. We only install simulator
    # requirements for the current platform.
    create_command.tools.host_arch = "wonky"

    first_app_generated.requires = ["something==1.2.3", "other>=2.3.4"]

    # Set a minimum OS version
    first_app_generated.min_os_version = "15.2"

    create_command.tools[first_app_generated].app_context = MagicMock(
        spec_set=Subprocess
    )

    create_command.install_app_requirements(first_app_generated)

    bundle_path = tmp_path / "base_path/build/first-app/ios/xcode"
    assert create_command.tools[first_app_generated].app_context.run.mock_calls == [
        call(
            [
                sys.executable,
                "-u",
                "-X",
                "utf8",
                "-m",
                "pip",
                "install",
                "--disable-pip-version-check",
                "--upgrade",
                "--no-user",
                f"--target={bundle_path / 'app_packages.iphoneos'}",
                "--only-binary=:all:",
                "--extra-index-url",
                "https://pypi.anaconda.org/beeware/simple",
                "--platform=ios_15_2_arm64_iphoneos",
                "something==1.2.3",
                "other>=2.3.4",
            ],
            check=True,
            encoding="UTF-8",
            env={
                "PYTHONPATH": str(
                    tmp_path
                    / "base_path/build/first-app/ios/xcode/Support"
                    / "Python.xcframework/ios-arm64"
                    / "platform-config/arm64-iphoneos"
                ),
                "PIP_REQUIRE_VIRTUALENV": None,
            },
        ),
        call(
            [
                sys.executable,
                "-u",
                "-X",
                "utf8",
                "-m",
                "pip",
                "install",
                "--disable-pip-version-check",
                "--upgrade",
                "--no-user",
                f"--target={bundle_path / 'app_packages.iphonesimulator'}",
                "--only-binary=:all:",
                "--extra-index-url",
                "https://pypi.anaconda.org/beeware/simple",
                "--platform=ios_15_2_wonky_iphonesimulator",
                "something==1.2.3",
                "other>=2.3.4",
            ],
            check=True,
            encoding="UTF-8",
            env={
                "PYTHONPATH": str(
                    tmp_path
                    / "base_path/build/first-app/ios/xcode/Support"
                    / "Python.xcframework/ios-arm64_x86_64-simulator"
                    / "platform-config/wonky-iphonesimulator"
                ),
                "PIP_REQUIRE_VIRTUALENV": None,
            },
        ),
    ]


def test_incompatible_min_os_version(create_command, first_app_generated, tmp_path):
    """If the app's iOS version isn't compatible with the support package, an error is raised."""
    # Hard code the current architecture for testing. We only install simulator
    # requirements for the current platform.
    create_command.tools.host_arch = "wonky"

    first_app_generated.requires = ["something==1.2.3", "other>=2.3.4"]
    first_app_generated.min_os_version = "8.0"

    create_command.tools[first_app_generated].app_context = MagicMock(
        spec_set=Subprocess
    )

    with pytest.raises(
        BriefcaseCommandError,
        match=(
            r"Your iOS app specifies a minimum iOS version of 8.0, "
            r"but the support package only supports 12.0"
        ),
    ):
        create_command.install_app_requirements(first_app_generated)

    create_command.tools[first_app_generated].app_context.run.assert_not_called()


@pytest.mark.parametrize(
    "permissions, info, context",
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


def test_install_app_requirements_error_adds_install_hint_missing_iphoneos_wheel(
    create_command, first_app_generated
):
    """Install_hint (mentioning a missing iphoneos wheel) is added when RequirementsInstallError is raised
    by _install_app_requirements in the iOS create command."""
    first_app_generated.min_os_version = "15.4"
    first_app_generated.requires = ["package-one", "package_two", "package_three"]

    # Mock app_context for the generated app to simulate pip failure
    mock_app_context = MagicMock(spec=Subprocess)
    mock_app_context.run.side_effect = CalledProcessError(returncode=1, cmd="pip")
    create_command.tools[first_app_generated].app_context = mock_app_context

    # Check that _install_app_requirements raises a RequirementsInstallError with an install hint
    with pytest.raises(
        RequirementsInstallError,
        match=(
            r"This may be because the `iphoneos` wheels that are available are not compatible\n"
            r"with a minimum iOS version of 15.4."
        ),
    ):
        create_command._install_app_requirements(
            app=first_app_generated,
            requires=first_app_generated.requires,
            app_packages_path=Path("/test/path"),
        )

    # Ensure the mocked subprocess was called as expected
    mock_app_context.run.assert_called_once()


def test_install_app_requirements_error_adds_install_hint_missing_iphonesimulator_wheel(
    create_command, first_app_generated
):
    """Install_hint (mentioning a missing iphonesimulator wheel) is added when RequirementsInstallError is raised
    by _install_app_requirements in the iOS create command."""
    first_app_generated.min_os_version = "15.4"
    first_app_generated.requires = ["package-one", "package_two", "package_three"]

    # Mock app_context for the generated app to simulate pip failure
    mock_app_context = MagicMock(spec=Subprocess)
    mock_app_context.run.side_effect = [
        None,
        CalledProcessError(returncode=1, cmd="pip"),
    ]
    create_command.tools[first_app_generated].app_context = mock_app_context

    # Check that _install_app_requirements raises a RequirementsInstallError with an install hint
    with pytest.raises(
        RequirementsInstallError,
        match=(
            r"This may indicate that an `iphoneos` wheel could be found, but an\n"
            r"`iphonesimulator` wheel could not be found; or that the `iphonesimulator`\n"
            r"binary wheels that are available are not compatible with a minimum iOS\n"
            r"version of 15.4.\n"
        ),
    ):
        create_command._install_app_requirements(
            app=first_app_generated,
            requires=first_app_generated.requires,
            app_packages_path=Path("/test/path"),
        )

    # Ensure the mocked subprocess was called as expected
    assert mock_app_context.run.call_count == 2
