from subprocess import CalledProcessError
from unittest.mock import MagicMock

import pytest

from briefcase.exceptions import BriefcaseCommandError
from briefcase.platforms.android.gradle import GradleRunCommand


@pytest.fixture
def run_command(tmp_path, first_app_config):
    command = GradleRunCommand(base_path=tmp_path / "base_path")
    command.dot_briefcase_path = tmp_path / ".briefcase"
    command.java_home_path = tmp_path / "java"

    command.mock_adb = MagicMock()
    command.ADB = MagicMock(return_value=command.mock_adb)

    command.os = MagicMock()
    command.os.environ = {}
    command.requests = MagicMock()
    command.subprocess = MagicMock()
    command.sys = MagicMock()
    return command


def test_verify_emulator_succeeds_immediately_if_emulator_installed(run_command):
    """`verify_emulator()` exits early if the emulator exists in its sdk_path."""
    # Create `emulator` within `sdk_path`.
    (run_command.sdk_path / "emulator").mkdir(parents=True)
    run_command.verify_emulator()
    run_command.subprocess.run.assert_not_called()
    run_command.requests.get.assert_not_called()


def test_verify_emulator_installs_android_emulator(run_command):
    """`verify_emulator()` calls `subprocess.run` with the parameters needed
    to install the Android emulator."""
    run_command.verify_emulator()
    run_command.subprocess.run.assert_called_once_with(
        [
            str(run_command.sdkmanager_path),
            "platforms;android-28",
            "system-images;android-28;default;x86",
            "emulator",
            "platform-tools",
        ],
        env=run_command.android_env,
        check=True,
    )


def test_verify_emulator_install_problems_are_reported(run_command):
    "If the sdkmanager fails to properly install the Android emulator, an exception is raised."
    # Configure `subprocess` module to crash as though it were a sad sdkmanager.
    run_command.subprocess.run.side_effect = CalledProcessError(
        returncode=1,
        cmd=["ignored"],
    )
    with pytest.raises(BriefcaseCommandError):
        run_command.verify_emulator()


def test_run_app_requires_device_name(run_command, first_app_config):
    """`run_app()` raises an exception if the user does not specify an Android device."""

    with pytest.raises(BriefcaseCommandError):
        run_command.run_app(first_app_config)

    # The ADB wrapper wasn't even created
    run_command.ADB.assert_not_called()


def test_run_app_launches_app_properly(run_command, first_app_config):
    """`run_app()` calls the appropriate `adb` integration commands."""
    # Invoke run_app
    run_command.run_app(first_app_config, "exampleDevice")

    # The ADB wrapper is created
    run_command.ADB.assert_called_once_with(
        sdk_path=run_command.sdk_path,
        device="exampleDevice",
    )

    # The adb wrapper is invoked with the expected arguments
    run_command.mock_adb.install_apk.assert_called_once_with(
        run_command.binary_path(first_app_config)
    )
    run_command.mock_adb.force_stop_app.assert_called_once_with(
        "{first_app_config.bundle}.{first_app_config.app_name}".format(
            first_app_config=first_app_config
        ),
    )
    run_command.mock_adb.start_app.assert_called_once_with(
        "{first_app_config.bundle}.{first_app_config.app_name}".format(
            first_app_config=first_app_config
        ),
        "org.beeware.android.MainActivity",
    )
