import os
import sys
from subprocess import CalledProcessError
from unittest.mock import MagicMock

import pytest
import requests

from briefcase.console import Console, Log
from briefcase.exceptions import BriefcaseCommandError
from briefcase.integrations.android_sdk import AndroidSDK
from briefcase.integrations.subprocess import Subprocess
from briefcase.platforms.android.gradle import GradleBuildCommand


@pytest.fixture
def build_command(tmp_path, first_app_config):
    command = GradleBuildCommand(
        logger=Log(),
        console=Console(),
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )
    command.tools.android_sdk = MagicMock(spec_set=AndroidSDK)
    command.tools.os = MagicMock(spec_set=os)
    command.tools.os.environ = {}
    command.tools.sys = MagicMock(spec_set=sys)
    command.tools.requests = MagicMock(spec_set=requests)
    command.tools.subprocess = MagicMock(spec_set=Subprocess)
    return command


@pytest.mark.parametrize(
    "host_os, gradlew_name",
    [("Windows", "gradlew.bat"), ("NonWindows", "gradlew")],
)
def test_execute_gradle(build_command, first_app_config, host_os, gradlew_name):
    """Validate that build_app() will launch `gradlew assembleDebug` with the
    appropriate environment & cwd, and that it will use `gradlew.bat` on
    Windows but `gradlew` elsewhere."""
    # Mock out `host_os` so we can validate which name is used for gradlew.
    build_command.tools.host_os = host_os
    # Create mock environment with `key`, which we expect to be preserved, and
    # `ANDROID_SDK_ROOT`, which we expect to be overwritten.
    build_command.tools.os.environ = {"ANDROID_SDK_ROOT": "somewhere", "key": "value"}
    build_command.build_app(first_app_config)
    build_command.tools.subprocess.run.assert_called_once_with(
        [
            build_command.bundle_path(first_app_config) / gradlew_name,
            "assembleDebug",
            "--console",
            "plain",
        ],
        cwd=build_command.bundle_path(first_app_config),
        env=build_command.tools.android_sdk.env,
        check=True,
    )


def test_print_gradle_errors(build_command, first_app_config):
    """Validate that build_app() will convert stderr/stdout from the process
    into exception text."""
    # Create a mock subprocess that crashes, printing text partly in non-ASCII.
    build_command.tools.subprocess.run.side_effect = CalledProcessError(
        returncode=1,
        cmd=["ignored"],
    )
    with pytest.raises(BriefcaseCommandError):
        build_command.build_app(first_app_config)
