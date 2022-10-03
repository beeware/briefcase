import sys
from unittest.mock import MagicMock

from briefcase.console import Console, Log
from briefcase.integrations.subprocess import Subprocess
from briefcase.platforms.iOS.xcode import iOSXcodeCreateCommand


def test_extra_pip_args(first_app_generated, tmp_path):
    """Extra iOS-specific args are included in calls to pip during update."""
    command = iOSXcodeCreateCommand(
        logger=Log(),
        console=Console(),
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )
    first_app_generated.requires = ["something==1.2.3", "other>=2.3.4"]

    command.tools[first_app_generated].app_context = MagicMock(spec_set=Subprocess)

    command.install_app_dependencies(first_app_generated)

    command.tools[first_app_generated].app_context.run.assert_called_once_with(
        [
            sys.executable,
            "-u",
            "-m",
            "pip",
            "install",
            "--upgrade",
            "--no-user",
            f"--target={tmp_path / 'base_path' / 'iOS' / 'Xcode' / 'First App' / 'app_packages'}",
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
                / "iOS"
                / "Xcode"
                / "First App"
                / "support"
                / "platform-site"
            )
        },
    )
