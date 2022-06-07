import os
import subprocess
from unittest.mock import MagicMock, call

import pytest

from briefcase.exceptions import BriefcaseCommandError, InvalidDeviceError
from briefcase.integrations.android_sdk import ADB, AndroidSDK


@pytest.fixture
def mock_sdk(tmp_path):
    command = MagicMock()
    command.host_platform = "unknown"

    sdk = AndroidSDK(command, jdk=MagicMock(), root_path=tmp_path)
    sdk.sleep = MagicMock()

    sdk.mock_run = MagicMock()

    def mock_adb(device):
        adb = ADB(sdk, device)
        adb.run = sdk.mock_run
        return adb

    sdk.adb = mock_adb

    # Mock some existing emulators
    sdk.emulators = MagicMock(
        return_value=[
            "runningEmulator",
            "idleEmulator",
        ]
    )

    return sdk


def test_invalid_emulator(mock_sdk):
    """Attempting to start an invalid emulator raises an error."""

    with pytest.raises(InvalidDeviceError):
        mock_sdk.start_emulator("no-such-avd")


def test_start_emulator(mock_sdk):
    """An emulator can be started."""
    # Mock 4 calls to devices.
    # First call returns 3 devices, but not the new emulator.
    # Second call returns the same thing.
    # Third call returns the new device in an offline state.
    # Last call returns the new device in an online state.
    devices = {
        "041234567892009a": {
            "name": "Unknown device (not authorized for development)",
            "authorized": False,
        },
        "KABCDABCDA1513": {
            "name": "Kogan Agora 9",
            "authorized": True,
        },
        "emulator-5554": {
            "name": "Android SDK built for x86",
            "authorized": True,
        },
    }
    devices_3 = devices.copy()
    devices_3["emulator-5556"] = {
        "name": "Unknown device (offline)",
        "authorized": False,
    }
    devices_4 = devices.copy()
    devices_4["emulator-5556"] = {
        "name": "generic_x86",
        "authorized": True,
    }

    # This will result in 4 calls to get devices
    mock_sdk.devices = MagicMock(
        side_effect=[
            devices,
            devices,
            devices_3,
            devices_4,
        ]
    )

    # There will be 5 calls on adb.run (3 calls to avd_name, then
    # 2 calls to getprop)
    mock_sdk.mock_run.side_effect = [
        # emu avd_name
        subprocess.CalledProcessError(returncode=1, cmd="emu avd name"),
        "runningEmulator\nOK",
        "idleEmulator\nOK",
        # shell getprop sys.boot_completed
        "\n",
        "1\n",
    ]

    # poll() on the process continues to return None, indicating no problem.
    emu_popen = MagicMock()
    emu_popen.poll.return_value = None
    mock_sdk.command.subprocess.Popen.return_value = emu_popen

    # Start the emulator
    device, name = mock_sdk.start_emulator("idleEmulator")

    # The device details are as expected
    assert device == "emulator-5556"
    assert name == "@idleEmulator (running emulator)"

    # The process was started.
    mock_sdk.command.subprocess.Popen.assert_called_with(
        [
            os.fsdecode(mock_sdk.emulator_path),
            "@idleEmulator",
            "-dns-server",
            "8.8.8.8",
        ],
        env=mock_sdk.env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        start_new_session=True,
    )

    # There were 5 calls to run
    mock_sdk.mock_run.assert_has_calls(
        [
            # Three calls to get avd name
            call("emu", "avd", "name"),
            call("emu", "avd", "name"),
            call("emu", "avd", "name"),
            # 2 calls to get boot property
            call("shell", "getprop", "sys.boot_completed"),
            call("shell", "getprop", "sys.boot_completed"),
        ]
    )

    # Took a total of 5 naps.
    assert mock_sdk.sleep.call_count == 4


def test_emulator_fail_to_start(mock_sdk):
    """If the emulator fails to start, and error is displayed."""
    # Mock 4 calls to devices.
    # First call returns 3 devices, but not the new emulator.
    # Second call returns the same thing.
    # Third call returns the new device in an offline state.
    # Last call returns the new device in an online state.
    devices = {
        "041234567892009a": {
            "name": "Unknown device (not authorized for development)",
            "authorized": False,
        },
        "KABCDABCDA1513": {
            "name": "Kogan Agora 9",
            "authorized": True,
        },
        "emulator-5554": {
            "name": "Android SDK built for x86",
            "authorized": True,
        },
    }
    devices_3 = devices.copy()
    devices_3["emulator-5556"] = {
        "name": "Unknown device (offline)",
        "authorized": False,
    }
    devices_4 = devices.copy()
    devices_4["emulator-5556"] = {
        "name": "generic_x86",
        "authorized": True,
    }

    # This will result in 4 calls to get devices
    mock_sdk.devices = MagicMock(
        side_effect=[
            devices,
            devices,
            devices_3,
            devices_4,
        ]
    )

    # This will result in 5 calls on adb.run (3 calls to avd_name, then
    # 2 calls to getprop)
    mock_sdk.mock_run.side_effect = [
        # emu avd_name
        subprocess.CalledProcessError(returncode=1, cmd="emu avd name"),
        "runningEmulator\nOK",
        "idleEmulator\nOK",
        # shell getprop sys.boot_completed
        "\n",
        "1\n",
    ]

    # poll() on the process returns None for the first two attempts, but then
    # returns 1 indicating failure.
    emu_popen = MagicMock()
    emu_popen.poll.side_effect = [None, None, 1]
    emu_popen.args = [mock_sdk.emulator_path, "@idleEmulator"]
    mock_sdk.command.subprocess.Popen.return_value = emu_popen

    # Start the emulator
    with pytest.raises(BriefcaseCommandError):
        mock_sdk.start_emulator("idleEmulator")

    # The process was started.
    mock_sdk.command.subprocess.Popen.assert_called_with(
        [
            os.fsdecode(mock_sdk.emulator_path),
            "@idleEmulator",
            "-dns-server",
            "8.8.8.8",
        ],
        env=mock_sdk.env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        start_new_session=True,
    )

    # There were 2 calls to run, both to get AVD name
    mock_sdk.mock_run.assert_has_calls(
        [
            call("emu", "avd", "name"),
            call("emu", "avd", "name"),
        ]
    )

    # Took a total of 2 naps before failing.
    assert mock_sdk.sleep.call_count == 2


def test_emulator_fail_to_boot(mock_sdk):
    """If the emulator fails to boot, and error is displayed."""
    # Mock 4 calls to devices.
    # First call returns 3 devices, but not the new emulator.
    # Second call returns the same thing.
    # Third call returns the new device in an offline state.
    # Last call returns the new device in an online state.
    devices = {
        "041234567892009a": {
            "name": "Unknown device (not authorized for development)",
            "authorized": False,
        },
        "KABCDABCDA1513": {
            "name": "Kogan Agora 9",
            "authorized": True,
        },
        "emulator-5554": {
            "name": "Android SDK built for x86",
            "authorized": True,
        },
    }
    devices_3 = devices.copy()
    devices_3["emulator-5556"] = {
        "name": "Unknown device (offline)",
        "authorized": False,
    }
    devices_4 = devices.copy()
    devices_4["emulator-5556"] = {
        "name": "Android SDK built for x86",
        "authorized": True,
    }

    # This will result in 4 calls to get devices
    mock_sdk.devices = MagicMock(
        side_effect=[
            devices,
            devices,
            devices_3,
            devices_4,
        ]
    )

    # This will result in 6 calls on adb.run
    # 3 calls to avd_name and then 3 calls to getprop
    mock_sdk.mock_run.side_effect = [
        # emu avd_name
        subprocess.CalledProcessError(returncode=1, cmd="emu avd name"),
        "runningEmulator\nOK",
        "idleEmulator\nOK",
        # shell getprop sys.boot_completed
        "\n",  # gets in to emulator has_booted() if block
        "\n",  # enters has_booted() while loop
        "\n",  # one loop waiting for simulator to finish booting
        "1\n",  # successful boot...except poll() will return non-None first raising failure
    ]

    # poll() on the process returns failure during simulator boot
    emu_popen = MagicMock()
    emu_popen.poll.side_effect = [
        None,  # in start loop without emulator in device list
        None,  # in start loop without emulator in device list
        None,  # in start loop with emulator in offline mode
        None,  # in start loop with emulator in online mode
        None,  # in boot loop waiting for emulator to finish booting
        1,  # invoke failure mode for simulator boot
    ]
    emu_popen.args = [mock_sdk.emulator_path, "@idleEmulator"]
    mock_sdk.command.subprocess.Popen.return_value = emu_popen

    # Start the emulator
    with pytest.raises(BriefcaseCommandError):
        mock_sdk.start_emulator("idleEmulator")

    # The process was started.
    mock_sdk.command.subprocess.Popen.assert_called_with(
        [
            os.fsdecode(mock_sdk.emulator_path),
            "@idleEmulator",
            "-dns-server",
            "8.8.8.8",
        ],
        env=mock_sdk.env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        start_new_session=True,
    )

    # There were 6 calls to run before failure
    mock_sdk.mock_run.assert_has_calls(
        [
            # 3 calls to get avd name
            call("emu", "avd", "name"),
            call("emu", "avd", "name"),
            call("emu", "avd", "name"),
            # 3 calls to get boot property (since boot fails
            # before last/fourth one would return success)
            call("shell", "getprop", "sys.boot_completed"),
            call("shell", "getprop", "sys.boot_completed"),
            call("shell", "getprop", "sys.boot_completed"),
        ]
    )

    # Took a total of 5 naps.
    assert mock_sdk.sleep.call_count == 5
