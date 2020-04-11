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
    command.android_sdk = MagicMock()
    command.android_sdk.adb.return_value = command.mock_adb

    command.os = MagicMock()
    command.os.environ = {}
    command.requests = MagicMock()
    command.subprocess = MagicMock()
    command.sys = MagicMock()
    return command


def test_run_app_requires_device_name(run_command, first_app_config):
    """`run_app()` raises an exception if the user does not specify an Android device."""

    with pytest.raises(BriefcaseCommandError):
        run_command.run_app(first_app_config)

    # The ADB wrapper wasn't even created
    run_command.mock_adb.assert_not_called()


def test_run_app_launches_app_properly(run_command, first_app_config):
    """`run_app()` calls the appropriate `adb` integration commands."""
    # Invoke run_app
    run_command.run_app(first_app_config, "exampleDevice")

    # The ADB wrapper is created
    run_command.android_sdk.adb.assert_called_once_with(run_command, device="exampleDevice")

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
