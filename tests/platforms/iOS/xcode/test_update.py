import shutil
import sys
from unittest.mock import MagicMock, call

import pytest

from briefcase.console import Console
from briefcase.integrations.subprocess import Subprocess
from briefcase.platforms.iOS.xcode import iOSXcodeUpdateCommand


@pytest.fixture
def update_command(tmp_path):
    return iOSXcodeUpdateCommand(
        console=Console(),
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )


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
    update_command,
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
    update_command.tools.host_arch = "wonky"

    first_app_generated.requires = ["something==1.2.3", "other>=2.3.4"]

    update_command.tools[first_app_generated].app_context = MagicMock(
        spec_set=Subprocess
    )

    update_command.install_app_requirements(first_app_generated)

    bundle_path = tmp_path / "base_path/build/first-app/ios/xcode"
    assert update_command.tools[first_app_generated].app_context.run.mock_calls == [
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
