import subprocess
from pathlib import Path

import pytest

from briefcase.exceptions import BriefcaseCommandError


def sdkmanager_result(name):
    """Load a sample sdkmanager --list_installed result file, and return the content."""
    samples = Path(__file__).parent / "sdkmanager"
    with (samples / (name + ".out")).open(encoding="utf-8") as sdkmanager_output_file:
        return sdkmanager_output_file.read()


def test_list_installed_system_images(mock_tools, android_sdk):
    """Returns a set of installed system image package identifiers."""

    mock_tools.subprocess.check_output.return_value = sdkmanager_result(
        "system_image_and_emulator"
    )

    result = android_sdk.list_installed_system_images()

    assert result == {"system-images;android-31;default;x86_64"}
    mock_tools.subprocess.check_output.assert_called_once_with(
        [android_sdk.sdkmanager_path, "--list_installed"],
        env=android_sdk.env,
    )


def test_no_installed_system_images(mock_tools, android_sdk):
    """If no system images are installed, an empty set is returned."""
    mock_tools.subprocess.check_output.return_value = sdkmanager_result("emulator_only")

    result = android_sdk.list_installed_system_images()

    assert result == set()


def test_list_installed_system_images_failure(mock_tools, android_sdk):
    """If sdkmanager fails, an error is raised."""
    mock_tools.subprocess.check_output.side_effect = subprocess.CalledProcessError(
        1, ""
    )

    with pytest.raises(BriefcaseCommandError):
        android_sdk.list_installed_system_images()
