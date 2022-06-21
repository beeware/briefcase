import os
import subprocess

import pytest

from briefcase.exceptions import BriefcaseCommandError


def test_succeeds_immediately_if_emulator_installed(mock_sdk):
    """`verify_emulator()` exits early if the emulator exists in its
    root_path."""
    # Create `emulator` within `root_path`.
    (mock_sdk.root_path / "emulator").mkdir(parents=True)

    # Also create the platforms folder
    (mock_sdk.root_path / "platforms").mkdir(parents=True)

    mock_sdk.verify_emulator()

    # Platforms folder still exists
    assert (mock_sdk.root_path / "platforms").exists()

    # No extra calls made
    mock_sdk.command.subprocess.run.assert_not_called()
    mock_sdk.command.requests.get.assert_not_called()


def test_creates_platforms_folder(mock_sdk):
    """If the platforms folder doesn't exist, it is created."""
    # Create `emulator` within `root_path`.
    (mock_sdk.root_path / "emulator").mkdir(parents=True)

    # Verify the emulator. This should create the missing platforms folder.
    mock_sdk.verify_emulator()

    # Platforms folder now exists
    assert (mock_sdk.root_path / "platforms").exists()

    # No extra calls made
    mock_sdk.command.subprocess.run.assert_not_called()
    mock_sdk.command.requests.get.assert_not_called()


def test_installs_android_emulator(mock_sdk):
    """The emulator tools will be installed if needed."""
    mock_sdk.verify_emulator()

    # Platforms folder now exists
    assert (mock_sdk.root_path / "platforms").exists()

    mock_sdk.command.subprocess.run.assert_called_once_with(
        [
            os.fsdecode(mock_sdk.sdkmanager_path),
            "platform-tools",
            "emulator",
        ],
        env=mock_sdk.env,
        check=True,
    )


def test_install_problems_are_reported(mock_sdk):
    """If the sdkmanager fails to properly install the Android emulator, an
    exception is raised."""
    # Configure `subprocess` module to crash as though it were a sad sdkmanager.
    mock_sdk.command.subprocess.run.side_effect = subprocess.CalledProcessError(
        returncode=1,
        cmd=["ignored"],
    )
    with pytest.raises(BriefcaseCommandError):
        mock_sdk.verify_emulator()
