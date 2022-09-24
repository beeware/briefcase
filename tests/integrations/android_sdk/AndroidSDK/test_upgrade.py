import os
import subprocess

import pytest

from briefcase.exceptions import BriefcaseCommandError


def test_upgrade(mock_tools, android_sdk):
    """sdkmanager can be used to upgrade the Android SDK."""
    android_sdk.upgrade()

    mock_tools.subprocess.run.assert_called_once_with(
        [os.fsdecode(android_sdk.sdkmanager_path), "--update"],
        env=android_sdk.env,
        check=True,
    )


def test_upgrade_failure(mock_tools, android_sdk):
    """If sdkmanager fails, an error is raised."""
    mock_tools.subprocess.run.side_effect = subprocess.CalledProcessError(1, "")
    with pytest.raises(BriefcaseCommandError):
        android_sdk.upgrade()

    mock_tools.subprocess.run.assert_called_once_with(
        [os.fsdecode(android_sdk.sdkmanager_path), "--update"],
        env=android_sdk.env,
        check=True,
    )
