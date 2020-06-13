from subprocess import CalledProcessError
from unittest.mock import MagicMock

import pytest

from briefcase.exceptions import BriefcaseCommandError
from briefcase.platforms.android.gradle import GradlePackageCommand


@pytest.fixture
def package_command(tmp_path, first_app_config):
    command = GradlePackageCommand(base_path=tmp_path / "base_path")
    command.dot_briefcase_path = tmp_path / ".briefcase"
    command.android_sdk = MagicMock()
    command.os = MagicMock()
    command.os.environ = {}
    command.sys = MagicMock()
    command.requests = MagicMock()
    command.subprocess = MagicMock()
    return command


@pytest.mark.parametrize(
    "host_os,gradlew_name", [("Windows", "gradlew.bat"), ("NonWindows", "gradlew")],
)
def test_execute_gradle(package_command, first_app_config, host_os, gradlew_name):
    """Validate that package_app() will launch `gradlew assembleRelease` with the
    appropriate environment & cwd, and that it will use `gradlew.bat` on Windows
    but `gradlew` elsewhere."""
    # Mock out `host_os` so we can validate which name is used for gradlew.
    package_command.host_os = host_os
    # Create mock environment with `key`, which we expect to be preserved, and
    # `ANDROID_SDK_ROOT`, which we expect to be overwritten.
    package_command.os.environ = {"ANDROID_SDK_ROOT": "somewhere", "key": "value"}
    package_command.package_app(first_app_config)
    package_command.subprocess.run.assert_called_once_with(
        [
            str(package_command.bundle_path(first_app_config) / gradlew_name),
            "assembleRelease",
        ],
        cwd=str(package_command.bundle_path(first_app_config)),
        env=package_command.android_sdk.env,
        check=True,
    )


def test_print_gradle_errors(package_command, first_app_config):
    """Validate that package_app() will convert stderr/stdout from the process
    into exception text."""
    # Create a mock subprocess that crashes, printing text partly in non-ASCII.
    package_command.subprocess.run.side_effect = CalledProcessError(
        returncode=1, cmd=["ignored"],
    )
    with pytest.raises(BriefcaseCommandError):
        package_command.package_app(first_app_config)
