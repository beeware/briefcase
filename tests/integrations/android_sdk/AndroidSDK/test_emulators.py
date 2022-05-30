import subprocess

import pytest

from briefcase.exceptions import BriefcaseCommandError


def test_no_emulators(mock_sdk):
    """If there are no emulators, an empty list is returned."""
    mock_sdk.command.subprocess.check_output.return_value = ""

    assert mock_sdk.emulators() == []


def test_one_emulator(mock_sdk):
    """If there is a single emulator, it is returned."""
    mock_sdk.command.subprocess.check_output.return_value = "first\n"

    assert mock_sdk.emulators() == ["first"]


def test_multiple_emulators(mock_sdk):
    """If there are multiple emulators, they are all returned."""
    mock_sdk.command.subprocess.check_output.return_value = "first\nsecond\nthird\n"

    assert mock_sdk.emulators() == ["first", "second", "third"]


def test_adb_error(mock_sdk):
    """If there is a problem invoking adb, an error is returned."""
    mock_sdk.command.subprocess.check_output.side_effect = (
        subprocess.CalledProcessError(returncode=69, cmd="adb devices -l")
    )

    with pytest.raises(BriefcaseCommandError):
        mock_sdk.emulators()
