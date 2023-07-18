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

from ....utils import create_file


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

    # Make sure the dist folder exists
    (tmp_path / "base_path" / "dist").mkdir(parents=True)
    return command


def test_unsupported_template_version(package_command, first_app_generated):
    """Error raised if template's target version is not supported."""
    # Mock the build command previously called
    create_file(package_command.binary_path(first_app_generated), content="")

    package_command.verify_app = MagicMock(wraps=package_command.verify_app)

    package_command._briefcase_toml.update(
        {first_app_generated: {"briefcase": {"target_epoch": "0.3.16"}}}
    )

    with pytest.raises(
        BriefcaseCommandError,
        match="The app template used to generate this app is not compatible",
    ):
        package_command(first_app_generated, packaging_format="aab")

    package_command.verify_app.assert_called_once_with(first_app_generated)


def test_packaging_formats(package_command):
    assert package_command.packaging_formats == ["aab"]


def test_default_packaging_format(package_command):
    assert package_command.default_packaging_format == "aab"


def test_distribution_path(package_command, first_app_config, tmp_path):
    assert (
        package_command.distribution_path(first_app_config)
        == tmp_path / "base_path" / "dist" / "First App-0.0.1.aab"
    )


@pytest.mark.parametrize(
    "host_os,gradlew_name",
    [("Windows", "gradlew.bat"), ("NonWindows", "gradlew")],
)
def test_execute_gradle(
    package_command,
    first_app_config,
    host_os,
    gradlew_name,
    tmp_path,
):
    """Validate that package_app() will launch `gradlew bundleRelease` with the
    appropriate environment & cwd, and that it will use `gradlew.bat` on Windows but
    `gradlew` elsewhere."""
    # Mock out `host_os` so we can validate which name is used for gradlew.
    package_command.tools.host_os = host_os

    # Set up a side effect of invoking gradle to create a bundle
    def create_bundle(*args, **kwargs):
        create_file(
            tmp_path
            / "base_path"
            / "build"
            / "first-app"
            / "android"
            / "gradle"
            / "app"
            / "build"
            / "outputs"
            / "bundle"
            / "release"
            / "app-release.aab",
            "Android release",
        )

    package_command.tools.subprocess.run.side_effect = create_bundle

    # Create mock environment with `key`, which we expect to be preserved, and
    # `ANDROID_SDK_ROOT`, which we expect to be overwritten.
    package_command.tools.os.environ = {"ANDROID_SDK_ROOT": "somewhere", "key": "value"}

    package_command.package_app(first_app_config)

    package_command.tools.android_sdk.verify_emulator.assert_called_once_with()
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

    # The release asset has been moved into the dist folder
    assert (tmp_path / "base_path" / "dist" / "First App-0.0.1.aab").exists()


def test_print_gradle_errors(package_command, first_app_config):
    """Validate that package_app() will convert stderr/stdout from the process into
    exception text."""
    # Create a mock subprocess that crashes, printing text partly in non-ASCII.
    package_command.tools.subprocess.run.side_effect = CalledProcessError(
        returncode=1,
        cmd=["ignored"],
    )
    with pytest.raises(BriefcaseCommandError):
        package_command.package_app(first_app_config)
