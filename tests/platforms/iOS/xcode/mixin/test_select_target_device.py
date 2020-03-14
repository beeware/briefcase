from unittest import mock

import pytest

from briefcase.commands.base import BaseCommand
from briefcase.exceptions import BriefcaseCommandError
from briefcase.platforms.iOS.xcode import iOSXcodeMixin


class DummyCommand(iOSXcodeMixin, BaseCommand):
    """
    A dummy command that includes the iOS XCode mixin.
    """
    command = 'dummy'

    def __init__(self, base_path, **kwargs):
        super().__init__(base_path=base_path, **kwargs)


@pytest.fixture
def dummy_command(tmp_path):
    cmd = DummyCommand(base_path=tmp_path)

    # Mock the options object
    cmd.options = mock.MagicMock()
    cmd.options.device = None

    # Mock get_simulators
    mock_get_simulators = mock.MagicMock()
    cmd.get_simulators = mock_get_simulators

    # Mock user input
    mock_input = mock.MagicMock()
    cmd.input = mock_input

    return cmd


def test_explicit_device_udid(dummy_command):
    "If the user nominates a device UDID at the command line, it is used."
    # get_simulators will return some options.
    dummy_command.get_simulators.return_value = {
        '13.2': {
            'C9A005C8-9468-47C5-8376-68A6E3408209': 'iPhone 8',
            '2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D': 'iPhone 11',
            'EEEBA06C-81F9-407C-885A-2261306DB2BE': 'iPhone 11 Pro Max',
        }
    }

    # The target device will be the one the user specified as an option.
    result = dummy_command.select_target_device('2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D')
    udid, iOS_version, device = result

    assert udid == '2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D'
    assert iOS_version == '13.2'
    assert device == 'iPhone 11'


def test_explicit_device_name(dummy_command):
    "If an explicit device name is provided (case insensitive) it is used."
    # get_simulators will return multiple options on 2 iOS versions.
    dummy_command.get_simulators.return_value = {
        '10.3': {
            '0BB80120-FA02-4597-A1BA-DB8CDE4F086D': 'iPhone 5s',
            'D7BBAD14-38FD-48F5-ACFD-B1193F829216': 'iPhone 6',
            '6998CA09-44B5-4963-8F80-265412D99683': 'iPhone 7',
            '68A6E340-8376-47C5-9468-C9A005C88209': 'iPhone 8',
        },
        '13.2': {
            'C9A005C8-9468-47C5-8376-68A6E3408209': 'iPhone 8',
            '2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D': 'iPhone 11',
            'EEEBA06C-81F9-407C-885A-2261306DB2BE': 'iPhone 11 Pro Max',
        }
    }

    # Try to load an iPhone 8.
    # It matches case insensitive, and finds the highest iOS version.
    udid, iOS_version, device = dummy_command.select_target_device('iphone 8')

    assert udid == 'C9A005C8-9468-47C5-8376-68A6E3408209'
    assert iOS_version == '13.2'
    assert device == 'iPhone 8'

    # User input was not solicited
    assert dummy_command.input.call_count == 0


def test_explicit_device_name_and_version(dummy_command):
    "If there are multiple options on multiple devices, two user inputs are needed."
    # get_simulators will return multiple options on 2 iOS versions.
    dummy_command.get_simulators.return_value = {
        '10.3': {
            '0BB80120-FA02-4597-A1BA-DB8CDE4F086D': 'iPhone 5s',
            'D7BBAD14-38FD-48F5-ACFD-B1193F829216': 'iPhone 6',
            '6998CA09-44B5-4963-8F80-265412D99683': 'iPhone 7',
            '68A6E340-8376-47C5-9468-C9A005C88209': 'iPhone 8',
        },
        '13.2': {
            'C9A005C8-9468-47C5-8376-68A6E3408209': 'iPhone 8',
            '2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D': 'iPhone 11',
            'EEEBA06C-81F9-407C-885A-2261306DB2BE': 'iPhone 11 Pro Max',
        }
    }

    # Specify an iPhone 8 on 10.3
    # It matches case insensitive, and finds the explicit iOS version.
    udid, iOS_version, device = dummy_command.select_target_device('iphone 8::10.3')

    assert udid == '68A6E340-8376-47C5-9468-C9A005C88209'
    assert iOS_version == '10.3'
    assert device == 'iPhone 8'

    # User input was not solicited
    assert dummy_command.input.call_count == 0


def test_invalid_explicit_device_udid(dummy_command):
    "If the user nominates an invalid device UDID, an error is raised"
    # get_simulators will some options.
    dummy_command.get_simulators.return_value = {
        '13.2': {
            'C9A005C8-9468-47C5-8376-68A6E3408209': 'iPhone 8',
            '2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D': 'iPhone 11',
            'EEEBA06C-81F9-407C-885A-2261306DB2BE': 'iPhone 11 Pro Max',
        }
    }

    # The user nominates a specific device that doesn't exist
    with pytest.raises(BriefcaseCommandError):
        dummy_command.select_target_device('deadbeef-dead-beef-cafe-deadbeefdead')

    # User input was not solicited
    assert dummy_command.input.call_count == 0


def test_invalid_explicit_device_name(dummy_command):
    "If the user nominates an invalid device name, an error is raised"
    # get_simulators will some options.
    dummy_command.get_simulators.return_value = {
        '13.2': {
            'C9A005C8-9468-47C5-8376-68A6E3408209': 'iPhone 8',
            '2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D': 'iPhone 11',
            'EEEBA06C-81F9-407C-885A-2261306DB2BE': 'iPhone 11 Pro Max',
        }
    }

    # The user nominates a specific device name that doesn't exist
    with pytest.raises(BriefcaseCommandError):
        dummy_command.select_target_device('iphone 99')

    # User input was not solicited
    assert dummy_command.input.call_count == 0


def test_invalid_explicit_device_name_and_version(dummy_command):
    "If the user nominates an invalid device name and version, an error is raised"
    # get_simulators will some options.
    dummy_command.get_simulators.return_value = {
        '13.2': {
            'C9A005C8-9468-47C5-8376-68A6E3408209': 'iPhone 8',
            '2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D': 'iPhone 11',
            'EEEBA06C-81F9-407C-885A-2261306DB2BE': 'iPhone 11 Pro Max',
        }
    }

    # The user nominates a valid device name, but on a version that
    # doesn't exist.
    with pytest.raises(BriefcaseCommandError):
        dummy_command.select_target_device('iphone 11::37.42')


def test_implied_device(dummy_command):
    "If there's only one device, no input is required; the device is returned."
    # get_simulators will return one option.
    dummy_command.get_simulators.return_value = {
        '13.2': {
            '2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D': 'iPhone 11',
        }
    }

    udid, iOS_version, device = dummy_command.select_target_device()

    assert udid == '2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D'
    assert iOS_version == '13.2'
    assert device == 'iPhone 11'

    # No user input was solicited
    dummy_command.input.assert_not_called()


def test_implied_os(dummy_command):
    "If there is only one OS option, it's implied."
    # get_simulators will return multiple options on 1 iOS version.
    dummy_command.get_simulators.return_value = {
        '13.2': {
            'C9A005C8-9468-47C5-8376-68A6E3408209': 'iPhone 8',
            '2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D': 'iPhone 11',
            'EEEBA06C-81F9-407C-885A-2261306DB2BE': 'iPhone 11 Pro Max',
        }
    }

    # Return option 2 (iPhone 11)
    dummy_command.input.return_value = '2'

    udid, iOS_version, device = dummy_command.select_target_device()

    assert udid == 'EEEBA06C-81F9-407C-885A-2261306DB2BE'
    assert iOS_version == '13.2'
    assert device == 'iPhone 11 Pro Max'

    # User input was solicited once
    assert dummy_command.input.call_count == 1


def test_multiple_os_implied_device(dummy_command):
    "If there are multiple OS options, but only one device on the chosen OS, device is implied."
    # get_simulators will return multiple options on 1 iOS version.
    dummy_command.get_simulators.return_value = {
        '10.3': {
            '0BB80120-FA02-4597-A1BA-DB8CDE4F086D': 'iPhone 5s',
            'D7BBAD14-38FD-48F5-ACFD-B1193F829216': 'iPhone 6',
            '6998CA09-44B5-4963-8F80-265412D99683': 'iPhone 7',
        },
        '13.2': {
            '2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D': 'iPhone 11',
        }
    }

    # Return option 1 (13.2)
    dummy_command.input.return_value = '2'

    # Device for iOS 13.2 is implied.
    udid, iOS_version, device = dummy_command.select_target_device()

    assert udid == '2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D'
    assert iOS_version == '13.2'
    assert device == 'iPhone 11'

    # User input was solicited once
    assert dummy_command.input.call_count == 1


def test_os_and_device_options(dummy_command):
    "If there are multiple options on multiple devices, two user inputs are needed."
    # get_simulators will return multiple options on 2 iOS versions.
    dummy_command.get_simulators.return_value = {
        '10.3': {
            '0BB80120-FA02-4597-A1BA-DB8CDE4F086D': 'iPhone 5s',
            'D7BBAD14-38FD-48F5-ACFD-B1193F829216': 'iPhone 6',
            '6998CA09-44B5-4963-8F80-265412D99683': 'iPhone 7',
        },
        '13.2': {
            'C9A005C8-9468-47C5-8376-68A6E3408209': 'iPhone 8',
            '2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D': 'iPhone 11',
            'EEEBA06C-81F9-407C-885A-2261306DB2BE': 'iPhone 11 Pro Max',
        }
    }

    # Return option 2 (13.2), then option 1 (iPhone 11)
    dummy_command.input.side_effect = ['2', '1']

    udid, iOS_version, device = dummy_command.select_target_device()

    assert udid == '2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D'
    assert iOS_version == '13.2'
    assert device == 'iPhone 11'

    # User input was solicited twice
    assert dummy_command.input.call_count == 2


def test_no_os_versions(dummy_command):
    "If there are no supported OS versions, raise an error."
    # get_simulators returns no valid iOS versions.
    dummy_command.get_simulators.return_value = {}

    with pytest.raises(BriefcaseCommandError):
        dummy_command.select_target_device()


def test_no_devices_for_os(dummy_command):
    "If there are no devices for an OS version, raise an error."
    # get_simulators returns no devices for iOS 13.2
    dummy_command.get_simulators.return_value = {
        '13.2': {}
    }

    with pytest.raises(BriefcaseCommandError):
        dummy_command.select_target_device()
