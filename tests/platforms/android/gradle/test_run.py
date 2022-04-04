from unittest.mock import MagicMock

import pytest

from briefcase.exceptions import BriefcaseCommandError
from briefcase.integrations.android_sdk import AndroidSDK
from briefcase.platforms.android.gradle import GradleRunCommand


@pytest.fixture
def run_command(tmp_path, first_app_config):
    command = GradleRunCommand(base_path=tmp_path / "base_path")
    command.dot_briefcase_path = tmp_path / ".briefcase"
    command.java_home_path = tmp_path / "java"

    command.mock_adb = MagicMock()
    command.android_sdk = AndroidSDK(command, jdk=MagicMock(), root_path=tmp_path)
    command.android_sdk.adb = MagicMock(return_value=command.mock_adb)

    command.os = MagicMock()
    command.os.environ = {}
    command.requests = MagicMock()
    command.subprocess = MagicMock()
    command.sys = MagicMock()
    return command


def test_run_existing_device(run_command, first_app_config):
    "An app can be run on an existing device"
    # Set up device selection to return a running physical device.
    run_command.android_sdk.select_target_device = MagicMock(
        return_value=("exampleDevice", 'ExampleDevice', None)
    )
    # Set up app config to have a `-` in the `bundle`, to ensure it gets
    # normalized into a `_` via `package_name`.
    first_app_config.bundle = 'com.ex-ample'

    # Invoke run_app
    run_command.run_app(first_app_config, device_or_avd="exampleDevice")

    # selecte_target_device was invoked with a specific device
    run_command.android_sdk.select_target_device.assert_called_once_with(
        device_or_avd="exampleDevice"
    )

    # The ADB wrapper is created
    run_command.android_sdk.adb.assert_called_once_with(device="exampleDevice")

    # The adb wrapper is invoked with the expected arguments
    run_command.mock_adb.install_apk.assert_called_once_with(
        run_command.binary_path(first_app_config)
    )
    run_command.mock_adb.force_stop_app.assert_called_once_with(
        "{first_app_config.package_name}.{first_app_config.module_name}".format(
            first_app_config=first_app_config
        ),
    )

    run_command.mock_adb.clear_log.assert_called_once()

    run_command.mock_adb.start_app.assert_called_once_with(
        "{first_app_config.package_name}.{first_app_config.module_name}".format(
            first_app_config=first_app_config
        ),
        "org.beeware.android.MainActivity",
    )

    run_command.mock_adb.logcat.assert_called_once()


def test_run_created_device(run_command, first_app_config):
    "If the user chooses to run on a newly created device, an error is raised (for now)"
    # Set up device selection to return a completely new device
    run_command.android_sdk.select_target_device = MagicMock(
        return_value=(None, None, None)
    )
    run_command.input = MagicMock(return_value='newDevice')

    with pytest.raises(BriefcaseCommandError):
        run_command.run_app(first_app_config)

    # The ADB wrapper wasn't even created
    run_command.mock_adb.assert_not_called()


def test_run_idle_device(run_command, first_app_config):
    "If the user chooses to run on an idle device, an error is raised (for now)"
    # Set up device selection to return a new device that has an AVD,
    # but not a device ID.
    run_command.android_sdk.select_target_device = MagicMock(
        return_value=(None, "exampleDevice", "exampleDevice")
    )

    with pytest.raises(BriefcaseCommandError):
        run_command.run_app(first_app_config)

    # The ADB wrapper wasn't even created
    run_command.mock_adb.assert_not_called()
