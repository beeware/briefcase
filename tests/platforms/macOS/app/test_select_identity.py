from unittest import mock

import pytest

from briefcase.exceptions import BriefcaseCommandError
from briefcase.platforms.macOS.app import macOSAppPackageCommand


class DummyPublishCommand(macOSAppPackageCommand):
    """
    A Publish command that overrides
    """

    def __init__(self, base_path, **kwargs):
        super().__init__(base_path=base_path, **kwargs)


@pytest.fixture
def dummy_command(tmp_path):
    cmd = DummyPublishCommand(base_path=tmp_path)

    # Mock the options object
    cmd.options = mock.MagicMock()
    cmd.options.device = None

    # Mock get_identities
    mock_get_identities = mock.MagicMock()
    cmd.get_identities = mock_get_identities

    # Mock user input
    mock_input = mock.MagicMock()
    cmd.input = mock_input

    return cmd


def test_explicit_identity_checksum(dummy_command):
    "If the user nominates an identity by checksum, it is used."
    # get_identities will return some options.
    dummy_command.get_identities.return_value = {
        '38EBD6F8903EC63C238B04C1067833814CE47CA3': "Developer ID Application: Example Corporation Ltd (Z2K4383DLE)",
        '11E77FB58F13F6108B38110D5D92233C58ED38C5': "iPhone Developer: Jane Smith (BXAH5H869S)",
    }

    # The identity will be the onethe user specified as an option.
    result = dummy_command.select_identity('11E77FB58F13F6108B38110D5D92233C58ED38C5')

    assert result == "iPhone Developer: Jane Smith (BXAH5H869S)"

    # User input was not solicited
    assert dummy_command.input.call_count == 0


def test_explicit_identity_name(dummy_command):
    "If the user nominates an identity by name, it is used."
    # get_identities will return some options.
    dummy_command.get_identities.return_value = {
        '38EBD6F8903EC63C238B04C1067833814CE47CA3': "Developer ID Application: Example Corporation Ltd (Z2K4383DLE)",
        '11E77FB58F13F6108B38110D5D92233C58ED38C5': "iPhone Developer: Jane Smith (BXAH5H869S)",
    }

    # The identity will be the onethe user specified as an option.
    result = dummy_command.select_identity("iPhone Developer: Jane Smith (BXAH5H869S)")

    assert result == "iPhone Developer: Jane Smith (BXAH5H869S)"

    # User input was not solicited
    assert dummy_command.input.call_count == 0


def test_invalid_identity_name(dummy_command):
    "If the user nominates an identity by name, it is used."
    # get_identities will return some options.
    dummy_command.get_identities.return_value = {
        '38EBD6F8903EC63C238B04C1067833814CE47CA3': "Developer ID Application: Example Corporation Ltd (Z2K4383DLE)",
        '11E77FB58F13F6108B38110D5D92233C58ED38C5': "iPhone Developer: Jane Smith (BXAH5H869S)",
    }

    # The identity will be the onethe user specified as an option.
    with pytest.raises(BriefcaseCommandError):
        dummy_command.select_identity("not-an-identity")

    # User input was not solicited
    assert dummy_command.input.call_count == 0


def test_implied_identity(dummy_command):
    "If there is only one identity, it is automatically picked."
    # get_identities will return some options.
    dummy_command.get_identities.return_value = {
        '11E77FB58F13F6108B38110D5D92233C58ED38C5': "iPhone Developer: Jane Smith (BXAH5H869S)",
    }

    result = dummy_command.select_identity()

    # The identity will be the only option available.
    assert result == "iPhone Developer: Jane Smith (BXAH5H869S)"

    # User input was not solicited
    assert dummy_command.input.call_count == 0


def test_selected_identity(dummy_command):
    "If there is only one identity, it is automatically picked."
    # get_identities will return some options.
    dummy_command.get_identities.return_value = {
        '38EBD6F8903EC63C238B04C1067833814CE47CA3': "Developer ID Application: Example Corporation Ltd (Z2K4383DLE)",
        '11E77FB58F13F6108B38110D5D92233C58ED38C5': "iPhone Developer: Jane Smith (BXAH5H869S)",
    }

    # Return option 2
    dummy_command.input.side_effect = ['2']

    result = dummy_command.select_identity()

    # The identity will be the only option available.
    assert result == "iPhone Developer: Jane Smith (BXAH5H869S)"

    # User input was solicited once
    assert dummy_command.input.call_count == 1
