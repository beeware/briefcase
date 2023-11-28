from subprocess import CalledProcessError
from unittest.mock import MagicMock

import pytest

from briefcase.console import LogLevel
from briefcase.exceptions import BriefcaseCommandError

from ....utils import create_file


@pytest.fixture
def first_app_aab(first_app_config):
    first_app_config.packaging_format = "aab"
    return first_app_config


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


def test_distribution_path(package_command, first_app_aab, tmp_path):
    assert (
        package_command.distribution_path(first_app_aab)
        == tmp_path / "base_path/dist/First App-0.0.1.aab"
    )


@pytest.mark.parametrize(
    "host_os, gradlew_name, tool_debug_mode",
    [
        ("Windows", "gradlew.bat", True),
        ("Windows", "gradlew.bat", False),
        ("NonWindows", "gradlew", True),
        ("NonWindows", "gradlew", False),
    ],
)
def test_execute_gradle(
    package_command,
    first_app_aab,
    host_os,
    gradlew_name,
    tool_debug_mode,
    tmp_path,
):
    """Validate that package_app() will launch `gradlew bundleRelease` with the
    appropriate environment & cwd, and that it will use `gradlew.bat` on Windows but
    `gradlew` elsewhere."""
    # Mock out `host_os` so we can validate which name is used for gradlew.
    package_command.tools.host_os = host_os

    # Enable verbose tool logging
    if tool_debug_mode:
        package_command.tools.logger.verbosity = LogLevel.DEEP_DEBUG

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

    package_command.package_app(first_app_aab)

    package_command.tools.android_sdk.verify_emulator.assert_called_once_with()
    package_command.tools.subprocess.run.assert_called_once_with(
        [
            package_command.bundle_path(first_app_aab) / gradlew_name,
            "--console",
            "plain",
        ]
        + (["--debug"] if tool_debug_mode else [])
        + ["bundleRelease"],
        cwd=package_command.bundle_path(first_app_aab),
        env=package_command.tools.android_sdk.env,
        check=True,
        encoding="ISO-42",
    )

    # The release asset has been moved into the dist folder
    assert (tmp_path / "base_path/dist/First App-0.0.1.aab").exists()


def test_print_gradle_errors(package_command, first_app_aab):
    """Validate that package_app() will convert stderr/stdout from the process into
    exception text."""
    # Create a mock subprocess that crashes, printing text partly in non-ASCII.
    package_command.tools.subprocess.run.side_effect = CalledProcessError(
        returncode=1,
        cmd=["ignored"],
    )
    with pytest.raises(BriefcaseCommandError):
        package_command.package_app(first_app_aab)
