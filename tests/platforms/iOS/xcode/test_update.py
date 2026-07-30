import shutil
from unittest import mock

import pytest

from briefcase.platforms.iOS.xcode import iOSXcodeUpdateCommand

from ....utils import create_file


@pytest.fixture
def update_command(dummy_console, tmp_path):
    return iOSXcodeUpdateCommand(
        console=dummy_console,
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )


@pytest.mark.parametrize(
    ("old_config", "device_config_path", "sim_config_path"),
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
def test_install_requirements(
    update_command,
    mock_venv,
    mock_sim_venv,
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
        # Create the old-style VERSIONS file with a deliberately weird min iOS version
        create_file(
            tmp_path / "base_path/build/first-app/ios/xcode/Support/VERSIONS",
            "\n".join(
                [
                    "Python version: 3.10.15",
                    "Build: b11",
                    "Min iOS version: 12.0",
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
    update_command.tools.host_arch = "wonky"
    update_command.create_app_environment = mock.MagicMock(return_value=mock_sim_venv)

    first_app_generated.requires = ["something==1.2.3", "other>=2.3.4"]

    update_command.install_app_requirements(first_app_generated, mock_venv)

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
        install_hint=mock.ANY,
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
        install_hint=mock.ANY,
    )
