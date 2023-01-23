import datetime
import os
import platform
import sys
import time
from os.path import normpath
from pathlib import Path
from unittest import mock

import pytest
import requests

from briefcase.console import Console, Log
from briefcase.exceptions import BriefcaseCommandError
from briefcase.integrations.android_sdk import ADB, AndroidSDK
from briefcase.integrations.java import JDK
from briefcase.integrations.subprocess import Subprocess
from briefcase.platforms.android.gradle import (
    GradleRunCommand,
    android_log_clean_filter,
)


@pytest.fixture
def jdk():
    jdk = mock.MagicMock()
    jdk.java_home = Path("/path/to/java")
    return jdk


@pytest.fixture
def run_command(tmp_path, first_app_config, jdk):
    command = GradleRunCommand(
        logger=Log(),
        console=Console(),
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )
    command.tools.mock_adb = mock.MagicMock(spec_set=ADB)
    command.tools.mock_adb.pidof = mock.MagicMock(return_value="777")
    command.tools.java = mock.MagicMock(spec=JDK)
    command.tools.java.java_home = "/path/to/java"
    command.tools.android_sdk = AndroidSDK(
        command.tools,
        root_path=Path("/path/to/android_sdk"),
    )
    command.tools.android_sdk.adb = mock.MagicMock(return_value=command.tools.mock_adb)

    command.tools.os = mock.MagicMock(spec_set=os)
    command.tools.os.environ = {}
    command.tools.requests = mock.MagicMock(spec_set=requests)
    command.tools.subprocess = mock.MagicMock(spec_set=Subprocess)
    command.tools.sys = mock.MagicMock(spec_set=sys)

    command._stream_app_logs = mock.MagicMock()

    command.base_path.mkdir(parents=True)
    return command


def test_binary_path(run_command, first_app_config, tmp_path):
    assert (
        run_command.binary_path(first_app_config)
        == tmp_path
        / "base_path"
        / "android"
        / "gradle"
        / "First App"
        / "app"
        / "build"
        / "outputs"
        / "apk"
        / "debug"
        / "app-debug.apk"
    )


def test_device_option(run_command):
    """The -d option can be parsed."""
    options = run_command.parse_options(["-d", "myphone"])

    assert options == {
        "device_or_avd": "myphone",
        "appname": None,
        "update": False,
        "update_requirements": False,
        "update_resources": False,
        "no_update": False,
        "test_mode": False,
        "extra_emulator_args": None,
        "shutdown_on_exit": False,
    }


def test_extra_emulator_args_option(run_command):
    """The -d option can be parsed."""
    options = run_command.parse_options(
        ["--Xemulator=-no-window", "--Xemulator=-no-audio"]
    )

    assert options == {
        "device_or_avd": None,
        "appname": None,
        "update": False,
        "update_requirements": False,
        "update_resources": False,
        "no_update": False,
        "test_mode": False,
        "extra_emulator_args": ["-no-window", "-no-audio"],
        "shutdown_on_exit": False,
    }


def test_shutdown_on_exit_option(run_command):
    """The -d option can be parsed."""
    options = run_command.parse_options(["--shutdown-on-exit"])

    assert options == {
        "device_or_avd": None,
        "appname": None,
        "update": False,
        "update_requirements": False,
        "update_resources": False,
        "no_update": False,
        "test_mode": False,
        "extra_emulator_args": None,
        "shutdown_on_exit": True,
    }


def test_run_existing_device(run_command, first_app_config):
    """An app can be run on an existing device."""
    # Set up device selection to return a running physical device.
    run_command.tools.android_sdk.select_target_device = mock.MagicMock(
        return_value=("exampleDevice", "ExampleDevice", None)
    )

    # Set up the log streamer to return a known stream
    log_popen = mock.MagicMock()
    run_command.tools.mock_adb.logcat.return_value = log_popen

    # To satisfy coverage, the stop function must be invoked at least once
    # when invoking stream_output.
    def mock_stream_output(app, stop_func, **kwargs):
        stop_func()

    run_command._stream_app_logs.side_effect = mock_stream_output

    # Set up app config to have a `-` in the `bundle`, to ensure it gets
    # normalized into a `_` via `package_name`.
    first_app_config.bundle = "com.ex-ample"

    # Invoke run_app
    run_command.run_app(
        first_app_config,
        device_or_avd="exampleDevice",
        test_mode=False,
    )

    # select_target_device was invoked with a specific device
    run_command.tools.android_sdk.select_target_device.assert_called_once_with(
        "exampleDevice"
    )

    # The ADB wrapper is created
    run_command.tools.android_sdk.adb.assert_called_once_with(device="exampleDevice")

    # The adb wrapper is invoked with the expected arguments
    run_command.tools.mock_adb.install_apk.assert_called_once_with(
        run_command.binary_path(first_app_config)
    )
    run_command.tools.mock_adb.force_stop_app.assert_called_once_with(
        f"{first_app_config.package_name}.{first_app_config.module_name}",
    )

    run_command.tools.mock_adb.start_app.assert_called_once_with(
        f"{first_app_config.package_name}.{first_app_config.module_name}",
        "org.beeware.android.MainActivity",
    )

    run_command.tools.mock_adb.pidof.assert_called_once_with(
        f"{first_app_config.package_name}.{first_app_config.module_name}",
        quiet=True,
    )
    run_command.tools.mock_adb.logcat.assert_called_once_with(pid="777")

    run_command._stream_app_logs.assert_called_once_with(
        first_app_config,
        popen=log_popen,
        test_mode=False,
        clean_filter=android_log_clean_filter,
        clean_output=False,
        stop_func=mock.ANY,
        log_stream=True,
    )

    # The emulator was not killed at the end of the test
    run_command.tools.mock_adb.kill.assert_not_called()


def test_run_slow_start(run_command, first_app_config, monkeypatch):
    """If the app is slow to start, multiple calls to pidof will be made."""
    run_command.tools.android_sdk.select_target_device = mock.MagicMock(
        return_value=("exampleDevice", "ExampleDevice", None)
    )

    # Set up the log streamer to return a known stream
    log_popen = mock.MagicMock()
    run_command.tools.mock_adb.logcat.return_value = log_popen

    # Mock the pidof call taking 3 attempts to return
    run_command.tools.mock_adb.pidof.side_effect = [None, None, "888"]
    monkeypatch.setattr(time, "sleep", mock.MagicMock())

    run_command.run_app(
        first_app_config,
        device_or_avd="exampleDevice",
        test_mode=False,
    )

    assert (
        run_command.tools.mock_adb.pidof.mock_calls
        == [mock.call("com.example.first_app", quiet=True)] * 3
    )
    assert time.sleep.mock_calls == [mock.call(0.01)] * 2
    run_command.tools.mock_adb.logcat.assert_called_once_with(pid="888")

    run_command._stream_app_logs.assert_called_once_with(
        first_app_config,
        popen=log_popen,
        test_mode=False,
        clean_filter=android_log_clean_filter,
        clean_output=False,
        stop_func=mock.ANY,
        log_stream=True,
    )


def test_run_crash_at_start(run_command, first_app_config, monkeypatch):
    """If the app crashes before a PID can be read, a log dump is shown."""
    run_command.tools.android_sdk.select_target_device = mock.MagicMock(
        return_value=("exampleDevice", "ExampleDevice", None)
    )

    # Mock the pidof call failing multiple times before a timeout.
    run_command.tools.mock_adb.pidof.side_effect = [None] * 5
    monkeypatch.setattr(time, "sleep", mock.MagicMock())

    # It's the eternal september...
    start_datetime = datetime.datetime(2022, 9, 8, 7, 6, 42)
    mock_datetime = mock.MagicMock(spec=datetime.datetime)
    # Mock datetime.now() at +0s, +0.5s, +1.5s,... +5.5s
    mock_datetime.now.side_effect = [
        start_datetime + datetime.timedelta(seconds=delay)
        for delay in [0] + [x + 0.5 for x in range(0, 6)]
    ]
    monkeypatch.setattr(datetime, "datetime", mock_datetime)

    with pytest.raises(
        BriefcaseCommandError, match=r"Problem starting app 'first-app'"
    ):
        run_command.run_app(
            first_app_config,
            device_or_avd="exampleDevice",
            test_mode=False,
        )

    assert (
        run_command.tools.mock_adb.pidof.mock_calls
        == [mock.call("com.example.first_app", quiet=True)] * 5
    )
    assert time.sleep.mock_calls == [mock.call(0.01)] * 5

    # The PID was never found, so logs can't be streamed
    run_command.tools.mock_adb.logcat.assert_not_called()

    # But we will get a log dump from logcat_tail
    run_command.tools.mock_adb.logcat_tail.assert_called_once_with(
        since=start_datetime - datetime.timedelta(seconds=10)
    )


def test_run_created_emulator(run_command, first_app_config):
    """The user can choose to run on a newly created emulator."""
    # Set up device selection to return a completely new emulator
    run_command.tools.android_sdk.select_target_device = mock.MagicMock(
        return_value=(None, None, None)
    )
    run_command.tools.android_sdk.create_emulator = mock.MagicMock(
        return_value="newDevice"
    )
    run_command.tools.android_sdk.verify_avd = mock.MagicMock()
    run_command.tools.android_sdk.start_emulator = mock.MagicMock(
        return_value=("emulator-3742", "New Device")
    )

    # Set up the log streamer to return a known stream
    log_popen = mock.MagicMock()
    run_command.tools.mock_adb.logcat.return_value = log_popen

    # Invoke run_app
    run_command.run_app(first_app_config, test_mode=False)

    # A new emulator was created
    run_command.tools.android_sdk.create_emulator.assert_called_once_with()

    # No attempt was made to verify the AVD (it is pre-verified through
    # the creation process)
    run_command.tools.android_sdk.verify_avd.assert_not_called()

    # The emulator was started
    run_command.tools.android_sdk.start_emulator.assert_called_once_with(
        "newDevice", None
    )

    # The ADB wrapper is created
    run_command.tools.android_sdk.adb.assert_called_once_with(device="emulator-3742")

    # The adb wrapper is invoked with the expected arguments
    run_command.tools.mock_adb.install_apk.assert_called_once_with(
        run_command.binary_path(first_app_config)
    )
    run_command.tools.mock_adb.force_stop_app.assert_called_once_with(
        f"{first_app_config.package_name}.{first_app_config.module_name}",
    )

    run_command.tools.mock_adb.start_app.assert_called_once_with(
        f"{first_app_config.package_name}.{first_app_config.module_name}",
        "org.beeware.android.MainActivity",
    )

    run_command.tools.mock_adb.logcat.assert_called_once_with(pid="777")

    run_command._stream_app_logs.assert_called_once_with(
        first_app_config,
        popen=log_popen,
        test_mode=False,
        clean_filter=android_log_clean_filter,
        clean_output=False,
        stop_func=mock.ANY,
        log_stream=True,
    )


def test_run_idle_device(run_command, first_app_config):
    """The user can choose to run on an idle device."""
    # Set up device selection to return a new device that has an AVD,
    # but not a device ID.
    run_command.tools.android_sdk.select_target_device = mock.MagicMock(
        return_value=(None, "Idle Device", "idleDevice")
    )

    run_command.tools.android_sdk.create_emulator = mock.MagicMock()
    run_command.tools.android_sdk.verify_avd = mock.MagicMock()
    run_command.tools.android_sdk.start_emulator = mock.MagicMock(
        return_value=("emulator-3742", "Idle Device")
    )

    # Set up the log streamer to return a known stream
    log_popen = mock.MagicMock()
    run_command.tools.mock_adb.logcat.return_value = log_popen

    # Invoke run_app
    run_command.run_app(first_app_config, test_mode=False)

    # No attempt was made to create a new emulator
    run_command.tools.android_sdk.create_emulator.assert_not_called()

    # The AVD has been verified
    run_command.tools.android_sdk.verify_avd.assert_called_with("idleDevice")

    # The emulator was started
    run_command.tools.android_sdk.start_emulator.assert_called_once_with(
        "idleDevice", None
    )

    # The ADB wrapper is created
    run_command.tools.android_sdk.adb.assert_called_once_with(device="emulator-3742")

    # The adb wrapper is invoked with the expected arguments
    run_command.tools.mock_adb.install_apk.assert_called_once_with(
        run_command.binary_path(first_app_config)
    )
    run_command.tools.mock_adb.force_stop_app.assert_called_once_with(
        f"{first_app_config.package_name}.{first_app_config.module_name}",
    )

    run_command.tools.mock_adb.start_app.assert_called_once_with(
        f"{first_app_config.package_name}.{first_app_config.module_name}",
        "org.beeware.android.MainActivity",
    )

    run_command.tools.mock_adb.logcat.assert_called_once_with(pid="777")

    run_command._stream_app_logs.assert_called_once_with(
        first_app_config,
        popen=log_popen,
        test_mode=False,
        clean_filter=android_log_clean_filter,
        clean_output=False,
        stop_func=mock.ANY,
        log_stream=True,
    )


def test_log_file_extra(run_command, monkeypatch):
    """Android commands register a log file extra to list SDK packages."""
    verify = mock.MagicMock(return_value=run_command.tools.android_sdk)
    monkeypatch.setattr(AndroidSDK, "verify", verify)
    monkeypatch.setattr(AndroidSDK, "verify_emulator", mock.MagicMock())

    # Even if one command triggers another, the sdkmanager should only be run once.
    run_command.update_command.verify_tools()
    run_command.verify_tools()

    sdk_manager = "/path/to/android_sdk/cmdline-tools/latest/bin/sdkmanager"
    if platform.system() == "Windows":
        sdk_manager += ".bat"

    run_command.tools.logger.save_log = True
    run_command.tools.subprocess.check_output.assert_not_called()
    run_command.tools.logger.save_log_to_file(run_command)
    run_command.tools.subprocess.check_output.assert_called_once_with(
        [normpath(sdk_manager), "--list_installed"],
        env={
            "ANDROID_SDK_ROOT": str(run_command.tools.android_sdk.root_path),
            "JAVA_HOME": str(run_command.tools.java.java_home),
        },
    )


def test_run_test_mode(run_command, first_app_config):
    """An app can be run in test mode."""
    # Set up device selection to return a running physical device.
    run_command.tools.android_sdk.select_target_device = mock.MagicMock(
        return_value=("exampleDevice", "ExampleDevice", None)
    )

    # Set up the log streamer to return a known stream
    log_popen = mock.MagicMock()
    run_command.tools.mock_adb.logcat.return_value = log_popen

    # To satisfy coverage, the stop function must be invoked at least once
    # when invoking stream_output.
    def mock_stream_output(app, stop_func, **kwargs):
        stop_func()

    run_command._stream_app_logs.side_effect = mock_stream_output

    # Set up app config to have a `-` in the `bundle`, to ensure it gets
    # normalized into a `_` via `package_name`.
    first_app_config.bundle = "com.ex-ample"

    # Invoke run_app
    run_command.run_app(
        first_app_config,
        device_or_avd="exampleDevice",
        test_mode=True,
        shutdown_on_exit=True,
    )

    # select_target_device was invoked with a specific device
    run_command.tools.android_sdk.select_target_device.assert_called_once_with(
        "exampleDevice"
    )

    # The ADB wrapper is created
    run_command.tools.android_sdk.adb.assert_called_once_with(device="exampleDevice")

    # The adb wrapper is invoked with the expected arguments
    run_command.tools.mock_adb.install_apk.assert_called_once_with(
        run_command.binary_path(first_app_config)
    )
    run_command.tools.mock_adb.force_stop_app.assert_called_once_with(
        f"{first_app_config.package_name}.{first_app_config.module_name}",
    )

    run_command.tools.mock_adb.start_app.assert_called_once_with(
        f"{first_app_config.package_name}.{first_app_config.module_name}",
        "org.beeware.android.MainActivity",
    )

    run_command.tools.mock_adb.pidof.assert_called_once_with(
        f"{first_app_config.package_name}.{first_app_config.module_name}",
        quiet=True,
    )
    run_command.tools.mock_adb.logcat.assert_called_once_with(pid="777")

    run_command._stream_app_logs.assert_called_once_with(
        first_app_config,
        popen=log_popen,
        test_mode=True,
        clean_filter=android_log_clean_filter,
        clean_output=False,
        stop_func=mock.ANY,
        log_stream=True,
    )

    # The emulator was killed at the end of the test
    run_command.tools.mock_adb.kill.assert_called_once_with()


def test_run_test_mode_created_emulator(run_command, first_app_config):
    """The user can choose to run in test mode on a newly created emulator."""
    # Set up device selection to return a completely new emulator
    run_command.tools.android_sdk.select_target_device = mock.MagicMock(
        return_value=(None, None, None)
    )
    run_command.tools.android_sdk.create_emulator = mock.MagicMock(
        return_value="newDevice"
    )
    run_command.tools.android_sdk.verify_avd = mock.MagicMock()
    run_command.tools.android_sdk.start_emulator = mock.MagicMock(
        return_value=("emulator-3742", "New Device")
    )

    # Set up the log streamer to return a known stream
    log_popen = mock.MagicMock()
    run_command.tools.mock_adb.logcat.return_value = log_popen

    # Invoke run_app
    run_command.run_app(
        first_app_config,
        test_mode=True,
        extra_emulator_args=["-no-window", "-no-audio"],
        shutdown_on_exit=True,
    )

    # A new emulator was created
    run_command.tools.android_sdk.create_emulator.assert_called_once_with()

    # No attempt was made to verify the AVD (it is pre-verified through
    # the creation process)
    run_command.tools.android_sdk.verify_avd.assert_not_called()

    # The emulator was started
    run_command.tools.android_sdk.start_emulator.assert_called_once_with(
        "newDevice",
        ["-no-window", "-no-audio"],
    )

    # The ADB wrapper is created
    run_command.tools.android_sdk.adb.assert_called_once_with(device="emulator-3742")

    # The adb wrapper is invoked with the expected arguments
    run_command.tools.mock_adb.install_apk.assert_called_once_with(
        run_command.binary_path(first_app_config)
    )
    run_command.tools.mock_adb.force_stop_app.assert_called_once_with(
        f"{first_app_config.package_name}.{first_app_config.module_name}",
    )

    run_command.tools.mock_adb.start_app.assert_called_once_with(
        f"{first_app_config.package_name}.{first_app_config.module_name}",
        "org.beeware.android.MainActivity",
    )

    run_command.tools.mock_adb.logcat.assert_called_once_with(pid="777")

    run_command._stream_app_logs.assert_called_once_with(
        first_app_config,
        popen=log_popen,
        test_mode=True,
        clean_filter=android_log_clean_filter,
        clean_output=False,
        stop_func=mock.ANY,
        log_stream=True,
    )

    # The emulator was killed at the end of the test
    run_command.tools.mock_adb.kill.assert_called_once_with()
