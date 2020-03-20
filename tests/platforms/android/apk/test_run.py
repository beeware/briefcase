from unittest.mock import MagicMock
from subprocess import CalledProcessError

import pytest

from briefcase.exceptions import BriefcaseCommandError
from briefcase.platforms.android.apk import ApkRunCommand


@pytest.fixture
def run_command(tmp_path, first_app_config):
    command = ApkRunCommand(base_path=tmp_path / "base_path")
    command.dot_briefcase_path = tmp_path / ".briefcase" / "tools"
    command.adb = MagicMock()
    command.os = MagicMock()
    command.os.environ = {}
    command.requests = MagicMock()
    command.subprocess = MagicMock()
    command.sys = MagicMock()
    return command


def test_verify_emulator_succeeds_immediately_if_emulator_installed(run_command):
    """Validate that verify_emulator() exits early, with no requests or subprocesses
    created, if the emulator exists in its sdk_path."""
    # Create `emulator` within `sdk_path`.
    (run_command.sdk_path / "emulator").mkdir(parents=True)
    run_command.verify_emulator()
    run_command.subprocess.check_output.assert_not_called()
    run_command.subprocess.run.assert_not_called()
    run_command.requests.get.assert_not_called()


def test_verify_emulator_installs_android_emulator(run_command):
    """Validate that the verify_emulator() method calls `subprocess.check_output`
    with the parameters needed to install the Android emulator."""
    run_command.verify_emulator()
    run_command.subprocess.check_output.assert_called_once_with(
        [
            str(run_command.sdk_path / "tools" / "bin" / "sdkmanager"),
            "platforms;android-28",
            "system-images;android-28;default;x86",
            "emulator",
            "platform-tools",
        ],
        stderr=run_command.subprocess.STDOUT,
    )


def test_verify_emulator_install_problems_are_reported(run_command):
    """Validate that if the Android `sdkmanager` fails to properly install the
    Android emulator, that we raise an appropriate exception with its output."""
    # Configure `subprocess` module to crash as though it were a sad sdkmanager.
    run_command.subprocess.check_output.side_effect = CalledProcessError(
        returncode=1,
        cmd=["ignored"],
        # `output` is non-ASCII to allow validation of Unicode errors.
        output=b"process output \xc3",
    )
    with pytest.raises(BriefcaseCommandError) as exc_info:
        run_command.verify_emulator()
    assert "process output �" in str(exc_info)


def test_run_app_requires_device_name(run_command, first_app_config):
    """Validate that `run_app()` raises an appropriate exception if the user
    does not pass `d` to specify an Android device."""
    with pytest.raises(BriefcaseCommandError):
        run_command.run_app(first_app_config)


def test_run_app_launches_app_properly(run_command, first_app_config):
    """Validate that `run_app()` calls the appropriate `adb` integration
    commands.

    Tests for the `adb` integration are done elsewhere."""
    run_command.run_app(first_app_config, "exampleDevice")
    run_command.adb.install_apk.assert_called_once_with(
        run_command.sdk_path, "exampleDevice", run_command.binary_path(first_app_config)
    )
    run_command.adb.force_stop_app.assert_called_once_with(
        run_command.sdk_path,
        "exampleDevice",
        "{first_app_config.bundle}.{first_app_config.app_name}".format(
            first_app_config=first_app_config
        ),
    )
    run_command.adb.start_app.assert_called_once_with(
        run_command.sdk_path,
        "exampleDevice",
        "{first_app_config.bundle}.{first_app_config.app_name}".format(
            first_app_config=first_app_config
        ),
        "org.beeware.android.MainActivity",
    )
