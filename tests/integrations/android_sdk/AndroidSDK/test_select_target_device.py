from unittest.mock import MagicMock

import pytest

from briefcase.exceptions import InvalidDeviceError
from briefcase.integrations.android_sdk import AndroidSDK, AndroidDeviceNotAuthorized


@pytest.fixture
def mock_sdk(tmp_path):
    command = MagicMock()
    sdk = AndroidSDK(command, root_path=tmp_path)

    sdk.devices = MagicMock(return_value={
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
    })

    sdk.emulators = MagicMock(return_value=[
        'runningEmulator',
        'idleEmulator',
    ])

    # Set up an ADB for each device.
    def mock_adb(device_id):
        adb = MagicMock()
        if device_id == 'emulator-5554':
            adb.avd_name.return_value = 'runningEmulator'
        else:
            adb.avd_name.return_value = None
        return adb

    sdk.adb = mock_adb

    return sdk


def test_explicit_device(mock_sdk):
    "If the user explicitly names a physical device, it is returned"

    # Select device with an explicit device ID
    device, name, avd = mock_sdk.select_target_device('KABCDABCDA1513')

    # Physical running device, so no AVD
    assert device == 'KABCDABCDA1513'
    assert name == 'Kogan_Agora_9'
    assert avd is None

    # No input was requested
    assert mock_sdk.command.input.call_count == 0


def test_explicit_unauthorized_device(mock_sdk):
    "If the user explicitly names an unauthorized physical device, an error is raised"

    # Select unauthorized device with an explicit device ID
    with pytest.raises(AndroidDeviceNotAuthorized):
        mock_sdk.select_target_device('041234567892009a')

    # No input was requested
    assert mock_sdk.command.input.call_count == 0


def test_explicit_running_emulator_by_id(mock_sdk):
    "If the user explicitly names a running emulator by device ID, it is selected"

    # Select emulator with an explicit device ID
    device, name, avd = mock_sdk.select_target_device('emulator-5554')

    # Emulator is running, so there is a device ID
    assert device == 'emulator-5554'
    assert name == '@runningEmulator (running generic_x86 emulator)'
    assert avd == "runningEmulator"

    # No input was requested
    assert mock_sdk.command.input.call_count == 0


def test_explicit_running_emulator_by_avd(mock_sdk):
    "If the user explicitly names a running emulator by AVD, it is selected"

    # Select emulator with an explicit device ID
    device, name, avd = mock_sdk.select_target_device('@runningEmulator')

    # Emulator is running, so there is a device ID
    assert device == 'emulator-5554'
    assert name == '@runningEmulator (running generic_x86 emulator)'
    assert avd == "runningEmulator"

    # No input was requested
    assert mock_sdk.command.input.call_count == 0


def test_explicit_idle_emulator(mock_sdk):
    "If the user explicitly names an idle emulator by AVD, it is selected"

    # Select emulator with an explicit device ID
    device, name, avd = mock_sdk.select_target_device('@idleEmulator')

    # Emulator is not running, so no device ID
    assert device is None
    assert name == '@idleEmulator (emulator)'
    assert avd == 'idleEmulator'

    # No input was requested
    assert mock_sdk.command.input.call_count == 0


def test_explicit_invalid_device(mock_sdk):
    "If the user explicitly names a non-existet device, an error is raised"

    # Select emulator with an invalid device ID
    with pytest.raises(InvalidDeviceError):
        device, name, avd = mock_sdk.select_target_device('deadbeefcafe')

    # No input was requested
    assert mock_sdk.command.input.call_count == 0


def test_explicit_invalid_avd(mock_sdk):
    "If the user explicitly names a non-existent device, an error is raised"

    # Select emulator with an invalid AVD
    with pytest.raises(InvalidDeviceError):
        device, name, avd = mock_sdk.select_target_device('@invalidEmulator')

    # No input was requested
    assert mock_sdk.command.input.call_count == 0


def test_select_device(mock_sdk, capsys):
    "If the user manually selects a physical device, details are returned"
    # Mock the user input
    mock_sdk.command.input.return_value = 1

    # Run the selection with no pre-existing choice
    device, name, avd = mock_sdk.select_target_device(None)

    # Physical running device, so no AVD
    assert device == 'KABCDABCDA1513'
    assert name == 'Kogan_Agora_9'
    assert avd is None

    # A re-run prompt has been provided
    out = capsys.readouterr().out
    assert "briefcase run android -d KABCDABCDA1513" in out


def test_select_unauthorized_device(mock_sdk):
    "If the user manually selects an unauthorized running device, an error is raised"
    # Mock the user input
    mock_sdk.command.input.return_value = 2

    # Run the selection with no pre-existing choice
    with pytest.raises(AndroidDeviceNotAuthorized):
        mock_sdk.select_target_device(None)


def test_select_running_emulator(mock_sdk, capsys):
    "If the user manually selects a running emulator, details are returned"
    # Mock the user input
    mock_sdk.command.input.return_value = 3

    # Run the selection with no pre-existing choice
    device, name, avd = mock_sdk.select_target_device(None)

    # Emulator is running, so there is a device ID
    assert device == 'emulator-5554'
    assert name == '@runningEmulator (running generic_x86 emulator)'
    assert avd == "runningEmulator"

    # A re-run prompt has been provided
    out = capsys.readouterr().out
    assert "briefcase run android -d @runningEmulator" in out


def test_select_idle_emulator(mock_sdk, capsys):
    "If the user manually selects a running device, details are returned"
    # Mock the user input
    mock_sdk.command.input.return_value = 4

    # Run the selection with no pre-existing choice
    device, name, avd = mock_sdk.select_target_device(None)

    # Emulator is not running, so no device ID
    assert device is None
    assert name == '@idleEmulator (emulator)'
    assert avd == 'idleEmulator'

    # A re-run prompt has been provided
    out = capsys.readouterr().out
    assert "briefcase run android -d @idleEmulator" in out


def test_select_create_emulator(mock_sdk, capsys):
    "If the user manually selects a running device, details are returned"
    # Mock the user input
    mock_sdk.command.input.return_value = 5

    # Run the selection with no pre-existing choice
    device, name, avd = mock_sdk.select_target_device(None)

    # No device details
    assert device is None
    assert name is None
    assert avd is None

    # A re-run prompt has *not* been provided
    out = capsys.readouterr().out
    assert "In future, you could specify this device" not in out
