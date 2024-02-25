import subprocess

import pytest

from briefcase.exceptions import BriefcaseCommandError


def test_no_avd_home(mock_tools, android_sdk):
    """If the AVD home directory doesn't exist, an empty list is returned."""
    assert not android_sdk.avd_home_path.is_dir()
    assert android_sdk.emulators() == []


def test_no_emulators(mock_tools, android_sdk):
    """If there are no emulators, an empty list is returned."""
    android_sdk.avd_home_path.mkdir(parents=True, exist_ok=True)
    mock_tools.subprocess.check_output.return_value = ""

    assert android_sdk.emulators() == []


def test_one_emulator(mock_tools, android_sdk):
    """If there is a single emulator, it is returned."""
    android_sdk.avd_home_path.mkdir(parents=True, exist_ok=True)
    mock_tools.subprocess.check_output.return_value = "first\n"

    assert android_sdk.emulators() == ["first"]


def test_multiple_emulators(mock_tools, android_sdk):
    """If there are multiple emulators, they are all returned."""
    android_sdk.avd_home_path.mkdir(parents=True, exist_ok=True)
    mock_tools.subprocess.check_output.return_value = "first\nsecond\nthird\n"

    assert android_sdk.emulators() == ["first", "second", "third"]


def test_adb_error(mock_tools, android_sdk):
    """If there is a problem invoking adb, an error is returned."""
    android_sdk.avd_home_path.mkdir(parents=True, exist_ok=True)
    mock_tools.subprocess.check_output.side_effect = subprocess.CalledProcessError(
        returncode=69, cmd="avdmanager list avd --compact"
    )

    with pytest.raises(BriefcaseCommandError):
        android_sdk.emulators()
