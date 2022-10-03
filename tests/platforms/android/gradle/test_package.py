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
from briefcase.platforms.android.gradle import GradlePackageCommand


@pytest.fixture
def package_command(tmp_path, first_app_config):
    command = GradlePackageCommand(
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


def test_packaging_formats(package_command):
    assert package_command.packaging_formats == ["aab"]


def test_default_packaging_format(package_command):
    assert package_command.default_packaging_format == "aab"


def test_distribution_path(package_command, first_app_config, tmp_path):
    assert (
        package_command.distribution_path(first_app_config, packaging_format="any")
        == tmp_path
        / "base_path"
        / "android"
        / "gradle"
        / "First App"
        / "app"
        / "build"
        / "outputs"
        / "bundle"
        / "release"
        / "app-release.aab"
    )


@pytest.mark.parametrize(
    "host_os,gradlew_name",
    [("Windows", "gradlew.bat"), ("NonWindows", "gradlew")],
)
def test_execute_gradle(package_command, first_app_config, host_os, gradlew_name):
    """Validate that package_app() will launch `gradlew bundleRelease` with the
    appropriate environment & cwd, and that it will use `gradlew.bat` on
    Windows but `gradlew` elsewhere."""
    # Mock out `host_os` so we can validate which name is used for gradlew.
    package_command.tools.host_os = host_os
    # Create mock environment with `key`, which we expect to be preserved, and
    # `ANDROID_SDK_ROOT`, which we expect to be overwritten.
    package_command.tools.os.environ = {"ANDROID_SDK_ROOT": "somewhere", "key": "value"}
    package_command.package_app(first_app_config)
    package_command.tools.subprocess.run.assert_called_once_with(
        [
            package_command.bundle_path(first_app_config) / gradlew_name,
            "bundleRelease",
            "--console",
            "plain",
        ],
        cwd=package_command.bundle_path(first_app_config),
        env=package_command.tools.android_sdk.env,
        check=True,
    )


def test_print_gradle_errors(package_command, first_app_config):
    """Validate that package_app() will convert stderr/stdout from the process
    into exception text."""
    # Create a mock subprocess that crashes, printing text partly in non-ASCII.
    package_command.tools.subprocess.run.side_effect = CalledProcessError(
        returncode=1,
        cmd=["ignored"],
    )
    with pytest.raises(BriefcaseCommandError):
        package_command.package_app(first_app_config)
