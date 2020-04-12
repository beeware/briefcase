import subprocess
from pathlib import Path

import pytest

from briefcase.exceptions import BriefcaseCommandError


def test_no_devices(mock_sdk):
    "If there are no devices, an empty list is returned"
    adb_samples = Path(__file__).parent / "devices"
    with (adb_samples / ("no_devices")).open("r") as adb_output_file:
        mock_sdk.command.subprocess.check_output.return_value = adb_output_file.read()

    assert mock_sdk.devices() == {}


def test_one_emulator(mock_sdk):
    "If there is a single emulator, it is returned"
    adb_samples = Path(__file__).parent / "devices"
    with (adb_samples / ("one_emulator")).open("r") as adb_output_file:
        mock_sdk.command.subprocess.check_output.return_value = adb_output_file.read()

    assert mock_sdk.devices() == {
        'emulator-5554': {
            'name': 'generic_x86',
            'authorized': True,
        },
    }


def test_multiple_devices(mock_sdk):
    "If there are multiple devices, they are all returned"
    adb_samples = Path(__file__).parent / "devices"
    with (adb_samples / ("multiple_devices")).open("r") as adb_output_file:
        mock_sdk.command.subprocess.check_output.return_value = adb_output_file.read()

    assert mock_sdk.devices() == {
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
        'emulator-5556': {
            'name': 'Unknown device (offline)',
            'authorized': False,
        },
    }


def test_adb_error(mock_sdk):
    "If there is a problem invoking adb, an error is returned"
    mock_sdk.command.subprocess.check_output.side_effect = subprocess.CalledProcessError(
        returncode=69, cmd="adb devices -l"
    )

    with pytest.raises(BriefcaseCommandError):
        mock_sdk.devices()
