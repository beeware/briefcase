import sys
from unittest.mock import MagicMock, call

import pytest

from briefcase.console import Console, Log
from briefcase.integrations.subprocess import Subprocess
from briefcase.platforms.iOS.xcode import iOSXcodeUpdateCommand


@pytest.fixture
def update_command(tmp_path):
    return iOSXcodeUpdateCommand(
        logger=Log(),
        console=Console(),
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )


def test_extra_pip_args(update_command, first_app_generated, tmp_path):
    """Extra iOS-specific args are included in calls to pip during update."""
    # Hard code the current architecture for testing. We only install simulator
    # requirements for the current platform.
    update_command.tools.host_arch = "wonky"

    first_app_generated.requires = ["something==1.2.3", "other>=2.3.4"]

    update_command.tools[first_app_generated].app_context = MagicMock(
        spec_set=Subprocess
    )

    update_command.install_app_requirements(first_app_generated, test_mode=False)

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
                "--no-python-version-warning",
                "--upgrade",
                "--no-user",
                f"--target={bundle_path / 'app_packages.iphoneos'}",
                "--prefer-binary",
                "--extra-index-url",
                "https://pypi.anaconda.org/beeware/simple",
                "something==1.2.3",
                "other>=2.3.4",
            ],
            check=True,
            encoding="UTF-8",
            env={
                "PYTHONPATH": str(
                    tmp_path
                    / "base_path"
                    / "build"
                    / "first-app"
                    / "ios"
                    / "xcode"
                    / "support"
                    / "platform-site"
                    / "iphoneos.arm64"
                )
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
                "--no-python-version-warning",
                "--upgrade",
                "--no-user",
                f"--target={bundle_path / 'app_packages.iphonesimulator'}",
                "--prefer-binary",
                "--extra-index-url",
                "https://pypi.anaconda.org/beeware/simple",
                "something==1.2.3",
                "other>=2.3.4",
            ],
            check=True,
            encoding="UTF-8",
            env={
                "PYTHONPATH": str(
                    tmp_path
                    / "base_path"
                    / "build"
                    / "first-app"
                    / "ios"
                    / "xcode"
                    / "support"
                    / "platform-site"
                    / "iphonesimulator.wonky"
                )
            },
        ),
    ]
