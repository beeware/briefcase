import os
import subprocess

import pytest

from briefcase.exceptions import BriefcaseCommandError


def test_list_packages(mock_tools, android_sdk):
    """sdkmanager can be used to list the packages managed by the Android
    SDK."""
    android_sdk.list_packages()

    mock_tools.subprocess.check_output.assert_called_once_with(
        [os.fsdecode(android_sdk.sdkmanager_path), "--list_installed"],
        env=android_sdk.env,
    )


def test_list_packages_failure(mock_tools, android_sdk):
    """If sdkmanager fails, an error is raised."""
    mock_tools.subprocess.check_output.side_effect = subprocess.CalledProcessError(
        1, ""
    )
    with pytest.raises(BriefcaseCommandError):
        android_sdk.list_packages()

    mock_tools.subprocess.check_output.assert_called_once_with(
        [os.fsdecode(android_sdk.sdkmanager_path), "--list_installed"],
        env=android_sdk.env,
    )
