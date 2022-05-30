import os
import subprocess

import pytest

from briefcase.exceptions import BriefcaseCommandError


def test_upgrade(mock_sdk):
    """sdkmanager can be use to upgrade the Android SDK."""
    mock_sdk.upgrade()

    mock_sdk.command.subprocess.run.assert_called_once_with(
        [os.fsdecode(mock_sdk.sdkmanager_path), "--update"],
        env=mock_sdk.env,
        check=True,
    )


def test_upgrade_failure(mock_sdk):
    """If sdkmanager fails, an error is raised."""
    mock_sdk.command.subprocess.run.side_effect = subprocess.CalledProcessError(1, "")
    with pytest.raises(BriefcaseCommandError):
        mock_sdk.upgrade()

    mock_sdk.command.subprocess.run.assert_called_once_with(
        [os.fsdecode(mock_sdk.sdkmanager_path), "--update"],
        env=mock_sdk.env,
        check=True,
    )
