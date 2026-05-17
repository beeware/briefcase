import subprocess

import pytest

from briefcase.exceptions import BriefcaseCommandError


def test_list_installed_system_images(mock_tools, android_sdk):
    """Returns a set of installed system image package identifiers."""
    mock_tools.subprocess.check_output.return_value = (
        "Installed packages:\n"
        "  Path                                    | Version | Description                    | Location\n"
        "  -------                                 | ------- | -------                        | -------\n"
        "  system-images;android-31;default;x86_64 | 5       | Intel x86_64 Atom System Image | system-images/android-31/default/x86_64\n"
        "  emulator                                | 35.4.9  | Android Emulator               | emulator\n"
    )

    result = android_sdk.list_installed_system_images()

    assert result == {"system-images;android-31;default;x86_64"}
    mock_tools.subprocess.check_output.assert_called_once_with(
        [android_sdk.sdkmanager_path, "--list_installed"],
        env=android_sdk.env,
    )


def test_no_installed_system_images(mock_tools, android_sdk):
    """If no system images are installed, an empty set is returned."""
    mock_tools.subprocess.check_output.return_value = (
        "Installed packages:\n"
        "  Path                                    | Version | Description                    | Location\n"
        "  -------                                 | ------- | -------                        | -------\n"
        "  emulator                                | 35.4.9  | Android Emulator               | emulator\n"
    )

    result = android_sdk.list_installed_system_images()

    assert result == set()


def test_list_installed_system_images_failure(mock_tools, android_sdk):
    """If sdkmanager fails, an error is raised."""
    mock_tools.subprocess.check_output.side_effect = subprocess.CalledProcessError(
        1, ""
    )

    with pytest.raises(BriefcaseCommandError):
        android_sdk.list_installed_system_images()
