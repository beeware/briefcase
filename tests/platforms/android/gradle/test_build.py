from subprocess import CalledProcessError
from unittest.mock import MagicMock

import pytest

from briefcase.exceptions import BriefcaseCommandError
from briefcase.platforms.android.gradle import GradleBuildCommand


@pytest.fixture
def build_command(tmp_path, first_app_config):
    command = GradleBuildCommand(base_path=tmp_path / "base_path")
    command.dot_briefcase_path = tmp_path / ".briefcase"
    command.android_sdk = MagicMock()
    command.os = MagicMock()
    command.os.environ = {}
    command.sys = MagicMock()
    command.requests = MagicMock()
    command.subprocess = MagicMock()
    return command


@pytest.mark.parametrize(
    "host_os,gradlew_name",
    [("Windows", "gradlew.bat"), ("NonWindows", "gradlew")],
)
def test_execute_gradle(build_command, first_app_config, host_os, gradlew_name):
    """Validate that build_app() will launch `gradlew assembleDebug` with the
    appropriate environment & cwd, and that it will use `gradlew.bat` on
    Windows but `gradlew` elsewhere."""
    # Mock out `host_os` so we can validate which name is used for gradlew.
    build_command.host_os = host_os
    # Create mock environment with `key`, which we expect to be preserved, and
    # `ANDROID_SDK_ROOT`, which we expect to be overwritten.
    build_command.os.environ = {"ANDROID_SDK_ROOT": "somewhere", "key": "value"}
    build_command.build_app(first_app_config)
    build_command.subprocess.run.assert_called_once_with(
        [
            build_command.bundle_path(first_app_config) / gradlew_name,
            "assembleDebug",
            "--console",
            "plain",
        ],
        cwd=build_command.bundle_path(first_app_config),
        env=build_command.android_sdk.env,
        check=True,
    )


def test_print_gradle_errors(build_command, first_app_config):
    """Validate that build_app() will convert stderr/stdout from the process
    into exception text."""
    # Create a mock subprocess that crashes, printing text partly in non-ASCII.
    build_command.subprocess.run.side_effect = CalledProcessError(
        returncode=1,
        cmd=["ignored"],
    )
    with pytest.raises(BriefcaseCommandError):
        build_command.build_app(first_app_config)
