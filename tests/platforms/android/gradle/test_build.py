from subprocess import CalledProcessError
from unittest.mock import MagicMock

import pytest

from briefcase.exceptions import BriefcaseCommandError
from briefcase.platforms.android.gradle import GradleBuildCommand


@pytest.fixture
def build_command(tmp_path, first_app_config):
    command = GradleBuildCommand(base_path=tmp_path / "base_path")
    command.dot_briefcase_path = tmp_path / ".briefcase"
    command.os = MagicMock()
    command.os.environ = {}
    command.sys = MagicMock()
    command.requests = MagicMock()
    command.subprocess = MagicMock()
    return command


def test_execute_gradle(build_command, first_app_config):
    """Validate that build_app() will launch `gradle assembleDebug` with the
    appropriate environment & cwd."""
    # Create mock environment with `key`, which we expect to be preserved, and
    # `ANDROID_SDK_ROOT`, which we expect to be overwritten.
    build_command.os.environ = {"ANDROID_SDK_ROOT": "somewhere", "key": "value"}
    build_command.build_app(first_app_config)
    build_command.subprocess.run.assert_called_once_with(
        ["./gradlew", "assembleDebug"],
        cwd=str(build_command.bundle_path(first_app_config)),
        env={"ANDROID_SDK_ROOT": str(build_command.sdk_path), "key": "value"},
        check=True,
    )


def test_print_gradle_errors(build_command, first_app_config):
    """Validate that build_app() will convert stderr/stdout from the process
    into exception text."""
    # Create a mock subprocess that crashes, printing text partly in non-ASCII.
    build_command.subprocess.run.side_effect = CalledProcessError(
        returncode=1, cmd=["ignored"],
    )
    with pytest.raises(BriefcaseCommandError):
        build_command.build_app(first_app_config)
