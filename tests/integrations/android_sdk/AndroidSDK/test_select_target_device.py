from unittest.mock import MagicMock

import pytest

from briefcase.exceptions import BriefcaseCommandError, InvalidDeviceError
from briefcase.integrations.android_sdk import (
    ADB,
    AndroidDeviceNotAuthorized,
    AndroidSDK,
)


@pytest.fixture
def android_sdk(android_sdk, tmp_path) -> AndroidSDK:
    android_sdk.devices = MagicMock(
        return_value={
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
    )

    android_sdk.emulators = MagicMock(
        return_value=[
            "runningEmulator",
            "idleEmulator",
        ]
    )

    # Set up an ADB for each device.
    def mock_adb(device_id):
        adb = MagicMock(spec_set=ADB)
        if device_id == "emulator-5554":
            adb.avd_name.return_value = "runningEmulator"
        else:
            adb.avd_name.return_value = None
        return adb

    android_sdk.adb = mock_adb

    return android_sdk


def test_explicit_device(mock_tools, android_sdk):
    """If the user explicitly names a physical device, it is returned."""

    # Select device with an explicit device ID
    device, name, avd = android_sdk.select_target_device("KABCDABCDA1513")

    # Physical running device, so no AVD
    assert device == "KABCDABCDA1513"
    assert name == "Kogan Agora 9 (KABCDABCDA1513)"
    assert avd is None

    # No input was requested
    assert mock_tools.input.prompts == []


def test_explicit_unauthorized_device(mock_tools, android_sdk):
    """If the user explicitly names an unauthorized physical device, an error is
    raised."""

    # Select unauthorized device with an explicit device ID
    with pytest.raises(AndroidDeviceNotAuthorized):
        android_sdk.select_target_device("041234567892009a")

    # No input was requested
    assert mock_tools.input.prompts == []


def test_explicit_running_emulator_by_id(mock_tools, android_sdk):
    """If the user explicitly names a running emulator by device ID, it is selected."""

    # Select emulator with an explicit device ID
    device, name, avd = android_sdk.select_target_device("emulator-5554")

    # Emulator is running, so there is a device ID
    assert device == "emulator-5554"
    assert name == "@runningEmulator (running emulator)"
    assert avd == "runningEmulator"

    # No input was requested
    assert mock_tools.input.prompts == []


def test_explicit_running_emulator_by_avd(mock_tools, android_sdk):
    """If the user explicitly names a running emulator by AVD, it is selected."""

    # Select emulator with an explicit device ID
    device, name, avd = android_sdk.select_target_device("@runningEmulator")

    # Emulator is running, so there is a device ID
    assert device == "emulator-5554"
    assert name == "@runningEmulator (running emulator)"
    assert avd == "runningEmulator"

    # No input was requested
    assert mock_tools.input.prompts == []


def test_explicit_idle_emulator(mock_tools, android_sdk):
    """If the user explicitly names an idle emulator by AVD, it is selected."""

    # Select emulator with an explicit device ID
    device, name, avd = android_sdk.select_target_device("@idleEmulator")

    # Emulator is not running, so no device ID
    assert device is None
    assert name == "@idleEmulator (emulator)"
    assert avd == "idleEmulator"

    # No input was requested
    assert mock_tools.input.prompts == []


def test_explicit_invalid_device(mock_tools, android_sdk):
    """If the user explicitly names a non-existet device, an error is raised."""

    # Select emulator with an invalid device ID
    with pytest.raises(InvalidDeviceError):
        device, name, avd = android_sdk.select_target_device("deadbeefcafe")

    # No input was requested
    assert mock_tools.input.prompts == []


def test_explicit_invalid_avd(mock_tools, android_sdk):
    """If the user explicitly names a non-existent device, an error is raised."""

    # Select emulator with an invalid AVD
    with pytest.raises(InvalidDeviceError):
        device, name, avd = android_sdk.select_target_device("@invalidEmulator")

    # No input was requested
    assert mock_tools.input.prompts == []


def test_select_device(mock_tools, android_sdk, capsys):
    """If the user manually selects a physical device, details are returned."""
    # Mock the user input
    mock_tools.input.values = ["2"]

    # Run the selection with no pre-existing choice
    device, name, avd = android_sdk.select_target_device(None)

    # Physical running device, so no AVD
    assert device == "KABCDABCDA1513"
    assert name == "Kogan Agora 9 (KABCDABCDA1513)"
    assert avd is None

    # The user was asked to select a device
    assert len(mock_tools.input.prompts) == 1

    # A re-run prompt has been provided
    out = capsys.readouterr().out
    assert "briefcase run android -d KABCDABCDA1513" in out


def test_select_unauthorized_device(mock_tools, android_sdk):
    """If the user manually selects an unauthorized running device, an error is
    raised."""
    # Mock the user input
    mock_tools.input.values = ["3"]

    # Run the selection with no pre-existing choice
    with pytest.raises(AndroidDeviceNotAuthorized):
        android_sdk.select_target_device(None)


def test_select_running_emulator(mock_tools, android_sdk, capsys):
    """If the user manually selects a running emulator, details are returned."""
    # Mock the user input
    mock_tools.input.values = ["1"]

    # Run the selection with no pre-existing choice
    device, name, avd = android_sdk.select_target_device(None)

    # Emulator is running, so there is a device ID
    assert device == "emulator-5554"
    assert name == "@runningEmulator (running emulator)"
    assert avd == "runningEmulator"

    # A re-run prompt has been provided
    out = capsys.readouterr().out
    assert 'briefcase run android -d "@runningEmulator"' in out


def test_select_idle_emulator(mock_tools, android_sdk, capsys):
    """If the user manually selects a running device, details are returned."""
    # Mock the user input
    mock_tools.input.values = ["4"]

    # Run the selection with no pre-existing choice
    device, name, avd = android_sdk.select_target_device(None)

    # Emulator is not running, so no device ID
    assert device is None
    assert name == "@idleEmulator (emulator)"
    assert avd == "idleEmulator"

    # A re-run prompt has been provided
    out = capsys.readouterr().out
    assert 'briefcase run android -d "@idleEmulator"' in out


def test_select_create_emulator(mock_tools, android_sdk, capsys):
    """If the user manually selects a running device, details are returned."""
    # Mock the user input
    mock_tools.input.values = ["5"]

    # Run the selection with no pre-existing choice
    device, name, avd = android_sdk.select_target_device(None)

    # No device details
    assert device is None
    assert name is None
    assert avd is None

    # A re-run prompt has *not* been provided
    out = capsys.readouterr().out
    assert "In future, you could specify this device" not in out


def test_input_disabled(mock_tools, android_sdk):
    """If input has been disabled, and there are multiple simulators, an error is
    raised."""
    mock_tools.input.enabled = False

    # Run the selection with no pre-existing choice
    with pytest.raises(BriefcaseCommandError):
        android_sdk.select_target_device(None)

    # No input was requested
    assert mock_tools.input.prompts == []


def test_input_disabled_no_simulators(mock_tools, android_sdk):
    """If input has been disabled, and there are no simulators, 'create' is selected."""
    mock_tools.input.enabled = False

    # Remove all the devices and emulators
    android_sdk.devices = MagicMock(return_value={})
    android_sdk.emulators = MagicMock(return_value=[])

    # Run the selection with no pre-existing choice
    device, name, avd = android_sdk.select_target_device(None)

    # No device details
    assert device is None
    assert name is None
    assert avd is None

    # No input was requested
    assert mock_tools.input.prompts == []


def test_input_disabled_one_device(mock_tools, android_sdk):
    """If input has been disabled, and there is a single device, it is selected."""
    mock_tools.input.enabled = False

    # Set up a single device.
    android_sdk.devices = MagicMock(
        return_value={
            "KABCDABCDA1513": {
                "name": "Kogan Agora 9",
                "authorized": True,
            },
        }
    )
    android_sdk.emulators = MagicMock(return_value=[])

    # Run the selection with no pre-existing choice
    device, name, avd = android_sdk.select_target_device(None)

    # The only device is returned
    assert device == "KABCDABCDA1513"
    assert name == "Kogan Agora 9 (KABCDABCDA1513)"
    assert avd is None

    # No input was requested
    assert mock_tools.input.prompts == []


def test_explicit_new_device(android_sdk):
    """If the user provides a device configuration, that configuration is created."""
    android_sdk._create_emulator = MagicMock()

    # Select a target device by providing a device config
    device, name, avd = android_sdk.select_target_device('{"avd":"myDevice"}')

    # A request was made to create the emulator using the internal method.
    android_sdk._create_emulator.assert_called_once_with(avd="myDevice")

    assert device is None
    assert name == "@myDevice (emulator)"
    assert avd == "myDevice"


def test_explicit_new_device_existing(android_sdk):
    """If the user provides a device configuration, that configuration is created."""
    android_sdk._create_emulator = MagicMock()

    # Select a target device by providing a device config
    device, name, avd = android_sdk.select_target_device('{"avd":"idleEmulator"}')

    # The emulator already exists, so it won't be created.
    android_sdk._create_emulator.assert_not_called()

    assert device is None
    assert name == "@idleEmulator (emulator)"
    assert avd == "idleEmulator"


def test_explicit_new_device_full_spec(android_sdk):
    """If the user provides a device configuration, that configuration is created."""
    android_sdk._create_emulator = MagicMock()

    # Select a target device by providing a device config
    device, name, avd = android_sdk.select_target_device(
        '{"avd":"myDevice","device_type":"pixel","skin":"pixel_6",'
        '"system_image":"system-images;android-21;default;arm64-v8a"}'
    )

    # A request was made to create the emulator using the internal method.
    android_sdk._create_emulator.assert_called_once_with(
        avd="myDevice",
        device_type="pixel",
        skin="pixel_6",
        system_image="system-images;android-21;default;arm64-v8a",
    )

    assert device is None
    assert name == "@myDevice (emulator)"
    assert avd == "myDevice"


def test_explicit_new_device_bad_spec(android_sdk):
    """If the user provides a bad device configuration, an error is raised."""
    android_sdk._create_emulator = MagicMock()

    # Select a target device by providing a device config
    with pytest.raises(
        BriefcaseCommandError,
        match=r"Unable to create emulator with definition '{NOT A JSON SNIPPET}'",
    ):
        android_sdk.select_target_device("{NOT A JSON SNIPPET}")


def test_explicit_new_device_incomplete_spec(android_sdk):
    """If the user provides a device configuration but doesn't provide an AVD, an error
    is raised."""
    android_sdk._create_emulator = MagicMock()

    # Select a target device by providing a device config
    with pytest.raises(
        BriefcaseCommandError,
        match=r"No AVD provided for new device",
    ):
        android_sdk.select_target_device('{"device_type":"pixel","skin":"pixel_3a"}')


def test_explicit_new_device_unknown_spec(android_sdk):
    """If the user provides a device configuration with an unknown argument, an error is
    raised."""

    def mock_create_emulator(avd, device_type=None, skin=None, system_image=None):
        pass

    android_sdk._create_emulator = MagicMock(side_effect=mock_create_emulator)

    # Select a target device by providing a device config
    with pytest.raises(
        BriefcaseCommandError,
        match=r"Unknown device property 'color'",
    ):
        android_sdk.select_target_device(
            '{"avd":"myPhone","device_type":"pixel","color":"blue"}'
        )
