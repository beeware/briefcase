import sys
from unittest.mock import MagicMock

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
    first_app_generated.requires = ["something==1.2.3", "other>=2.3.4"]

    update_command.tools[first_app_generated].app_context = MagicMock(
        spec_set=Subprocess
    )

    update_command.install_app_requirements(first_app_generated, test_mode=False)

    update_command.tools[first_app_generated].app_context.run.assert_called_once_with(
        [
            sys.executable,
            "-u",
            "-m",
            "pip",
            "install",
            "--upgrade",
            "--no-user",
            f"--target={tmp_path / 'base_path' / 'build' / 'first-app' / 'ios' / 'xcode' / 'app_packages'}",
            "--prefer-binary",
            "--extra-index-url",
            "https://pypi.anaconda.org/beeware/simple",
            "something==1.2.3",
            "other>=2.3.4",
        ],
        check=True,
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
            )
        },
    )
