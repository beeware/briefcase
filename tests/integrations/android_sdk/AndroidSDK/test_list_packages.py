import os
import subprocess

import pytest

from briefcase.exceptions import BriefcaseCommandError


def test_list_packages(mock_sdk):
    """sdkmanager can be use to list the packages managed by the Android
    SDK."""
    mock_sdk.list_packages()

    mock_sdk.command.subprocess.check_output.assert_called_once_with(
        [os.fsdecode(mock_sdk.sdkmanager_path), "--list_installed"],
        env=mock_sdk.env,
    )


def test_list_packages_failure(mock_sdk):
    """If sdkmanager fails, an error is raised."""
    mock_sdk.command.subprocess.check_output.side_effect = (
        subprocess.CalledProcessError(1, "")
    )
    with pytest.raises(BriefcaseCommandError):
        mock_sdk.list_packages()

    mock_sdk.command.subprocess.check_output.assert_called_once_with(
        [os.fsdecode(mock_sdk.sdkmanager_path), "--list_installed"],
        env=mock_sdk.env,
    )
