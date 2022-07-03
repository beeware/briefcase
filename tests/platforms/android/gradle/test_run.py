from unittest.mock import MagicMock

import pytest

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
    """An app can be run on an existing device."""
    # Set up device selection to return a running physical device.
    run_command.android_sdk.select_target_device = MagicMock(
        return_value=("exampleDevice", "ExampleDevice", None)
    )
    # Set up app config to have a `-` in the `bundle`, to ensure it gets
    # normalized into a `_` via `package_name`.
    first_app_config.bundle = "com.ex-ample"

    # Invoke run_app
    run_command.run_app(first_app_config, device_or_avd="exampleDevice")

    # select_target_device was invoked with a specific device
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
        f"{first_app_config.package_name}.{first_app_config.module_name}",
    )

    run_command.mock_adb.clear_log.assert_called_once()

    run_command.mock_adb.start_app.assert_called_once_with(
        f"{first_app_config.package_name}.{first_app_config.module_name}",
        "org.beeware.android.MainActivity",
    )

    run_command.mock_adb.logcat.assert_called_once()


def test_run_created_emulator(run_command, first_app_config):
    """The user can choose to run on a newly created emulator."""
    # Set up device selection to return a completely new emulator
    run_command.android_sdk.select_target_device = MagicMock(
        return_value=(None, None, None)
    )
    run_command.android_sdk.create_emulator = MagicMock(return_value="newDevice")
    run_command.android_sdk.verify_avd = MagicMock()
    run_command.android_sdk.start_emulator = MagicMock(
        return_value=("emulator-3742", "New Device")
    )

    # Invoke run_app
    run_command.run_app(first_app_config)

    # A new emulator was created
    run_command.android_sdk.create_emulator.assert_called_once_with()

    # No attempt was made to verify the AVD (it is pre-verified through
    # the creation process)
    run_command.android_sdk.verify_avd.assert_not_called()

    # The emulator was started
    run_command.android_sdk.start_emulator.assert_called_once_with("newDevice")

    # The ADB wrapper is created
    run_command.android_sdk.adb.assert_called_once_with(device="emulator-3742")

    # The adb wrapper is invoked with the expected arguments
    run_command.mock_adb.install_apk.assert_called_once_with(
        run_command.binary_path(first_app_config)
    )
    run_command.mock_adb.force_stop_app.assert_called_once_with(
        f"{first_app_config.package_name}.{first_app_config.module_name}",
    )

    run_command.mock_adb.clear_log.assert_called_once()

    run_command.mock_adb.start_app.assert_called_once_with(
        f"{first_app_config.package_name}.{first_app_config.module_name}",
        "org.beeware.android.MainActivity",
    )

    run_command.mock_adb.logcat.assert_called_once()


def test_run_idle_device(run_command, first_app_config):
    """The user can choose to run on an idle device."""
    # Set up device selection to return a new device that has an AVD,
    # but not a device ID.
    run_command.android_sdk.select_target_device = MagicMock(
        return_value=(None, "Idle Device", "idleDevice")
    )

    run_command.android_sdk.create_emulator = MagicMock()
    run_command.android_sdk.verify_avd = MagicMock()
    run_command.android_sdk.start_emulator = MagicMock(
        return_value=("emulator-3742", "Idle Device")
    )

    # Invoke run_app
    run_command.run_app(first_app_config)

    # No attempt was made to create a new emulator
    run_command.android_sdk.create_emulator.assert_not_called()

    # The AVD has been verified
    run_command.android_sdk.verify_avd.assert_called_with("idleDevice")

    # The emulator was started
    run_command.android_sdk.start_emulator.assert_called_once_with("idleDevice")

    # The ADB wrapper is created
    run_command.android_sdk.adb.assert_called_once_with(device="emulator-3742")

    # The adb wrapper is invoked with the expected arguments
    run_command.mock_adb.install_apk.assert_called_once_with(
        run_command.binary_path(first_app_config)
    )
    run_command.mock_adb.force_stop_app.assert_called_once_with(
        f"{first_app_config.package_name}.{first_app_config.module_name}",
    )

    run_command.mock_adb.clear_log.assert_called_once()

    run_command.mock_adb.start_app.assert_called_once_with(
        f"{first_app_config.package_name}.{first_app_config.module_name}",
        "org.beeware.android.MainActivity",
    )

    run_command.mock_adb.logcat.assert_called_once()
