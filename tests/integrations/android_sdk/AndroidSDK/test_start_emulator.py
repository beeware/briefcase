import subprocess
from unittest.mock import MagicMock, call

import pytest

from briefcase.exceptions import InvalidDeviceError
from briefcase.integrations.android_sdk import AndroidSDK, ADB


@pytest.fixture
def mock_sdk(tmp_path):
    command = MagicMock()
    command.host_platform = 'unknown'

    sdk = AndroidSDK(command, root_path=tmp_path)
    sdk.sleep = MagicMock()

    sdk.mock_run = MagicMock()

    def mock_adb(device):
        adb = ADB(sdk, device)
        adb.run = sdk.mock_run
        return adb
    sdk.adb = mock_adb

    # Mock some existing emulators
    sdk.emulators = MagicMock(return_value=[
        'runningEmulator',
        'idleEmulator',
    ])

    return sdk


def test_invalid_emulator(mock_sdk):
    "Attempting to start an invalid emulator raises an error."

    with pytest.raises(InvalidDeviceError):
        mock_sdk.start_emulator('no-such-avd')


def test_start_emulator(mock_sdk):
    "An emulator can be started"
    # Mock 4 calls to devices.
    # First call returns 3 devices, but not the new emulator.
    # Second call returns the same thing.
    # Third call returns the new device in an offline state.
    # Last call returns the new device in an online state.
    devices = {
        '041234567892009a': {
            'name': 'Unknown device (not authorized for development)',
            'authorized': False,
        },
        'KABCDABCDA1513': {
            'name': 'Kogan_Agora_9',
            'authorized': True,
        },
        'emulator-5554': {
            'name': 'generic_x86',
            'authorized': True,
        },
    }
    devices_3 = devices.copy()
    devices_3['emulator-5556'] = {
        'name': 'Unknown device (offline)',
        'authorized': False,
    }
    devices_4 = devices.copy()
    devices_4['emulator-5556'] = {
        'name': 'generic_x86',
        'authorized': True,
    }

    # This will result in
    mock_sdk.devices = MagicMock(side_effect=[
        devices, devices, devices_3, devices_4,
    ])

    # This will result in 5 calls on adb.run (3 calls to avd_name, then
    # 2 calls to getprop)
    mock_sdk.mock_run.side_effect = [
        # emu avd_name
        subprocess.CalledProcessError(
           returncode=1, cmd='emu avd name'
        ),
        'runningEmulator\nOK',
        'idleEmulator\nOK',
        # shell getprop sys.boot_completed
        '\n', "1\n",
    ]

    device, name = mock_sdk.start_emulator('idleEmulator')

    # The device details are as expected
    assert device == 'emulator-5556'
    assert name == '@idleEmulator (generic_x86 emulator)'

    # The process was started.
    mock_sdk.command.subprocess.Popen.assert_called_with(
        [
            mock_sdk.emulator_path,
            '@idleEmulator',
            '-dns-server', '8.8.8.8',
        ],
        env=mock_sdk.env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    # There were 5 calls to run
    mock_sdk.mock_run.assert_has_calls([
        # Three calls to get avd name
        call('emu', 'avd', 'name'),
        call('emu', 'avd', 'name'),
        call('emu', 'avd', 'name'),
        # 2 calls to get boot property
        call('shell', 'getprop', 'sys.boot_completed'),
        call('shell', 'getprop', 'sys.boot_completed'),
    ])

    # Took a total of 5 naps.
    assert mock_sdk.sleep.call_count == 5
