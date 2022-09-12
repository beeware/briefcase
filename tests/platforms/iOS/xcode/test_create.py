import sys
from unittest import mock

from briefcase.platforms.iOS.xcode import iOSXcodeCreateCommand


def test_extra_pip_args(first_app_generated, tmp_path):
    """Extra iOS-specific args are included in calls to pip during update."""
    command = iOSXcodeCreateCommand(base_path=tmp_path)
    first_app_generated.requires = ["something==1.2.3", "other>=2.3.4"]

    command.subprocess = mock.MagicMock()

    command.install_app_dependencies(first_app_generated)

    command.subprocess.run.assert_called_once_with(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--upgrade",
            "--no-user",
            f"--target={tmp_path / 'iOS' / 'Xcode' / 'First App' / 'app_packages'}",
            "--prefer-binary",
            "--extra-index-url",
            "https://pypi.anaconda.org/beeware/simple",
            "something==1.2.3",
            "other>=2.3.4",
        ],
        check=True,
        env={
            "PYTHONPATH": str(
                tmp_path / "iOS" / "Xcode" / "First App" / "support" / "platform-site"
            )
        },
    )
