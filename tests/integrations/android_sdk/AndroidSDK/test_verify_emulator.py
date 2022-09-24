import os
import subprocess
import sys

import pytest

from briefcase.exceptions import BriefcaseCommandError

from ....utils import create_file


def create_emulator(root_path):
    # Create `emulator` within `root_path`.
    if sys.platform == "win32":
        emulator_bin = "emulator.exe"
    else:
        emulator_bin = "emulator"

    create_file(root_path / "emulator" / emulator_bin, "The Emulator", chmod=0o755)


def test_succeeds_immediately_if_emulator_installed(mock_tools, android_sdk):
    """`verify_emulator()` exits early if the emulator exists in its
    root_path."""
    # Create `emulator` within `root_path`.
    create_emulator(android_sdk.root_path)

    # Also create the platforms folder
    (android_sdk.root_path / "platforms").mkdir(parents=True)

    android_sdk.verify_emulator()

    # Platforms folder still exists
    assert (android_sdk.root_path / "platforms").exists()

    # No extra calls made
    mock_tools.subprocess.run.assert_not_called()
    mock_tools.download.file.assert_not_called()


def test_creates_platforms_folder(mock_tools, android_sdk):
    """If the platforms folder doesn't exist, it is created."""
    # Create `emulator` within `root_path`.
    create_emulator(android_sdk.root_path)

    # Verify the emulator. This should create the missing platforms folder.
    android_sdk.verify_emulator()

    # Platforms folder now exists
    assert (android_sdk.root_path / "platforms").exists()

    # No extra calls made
    mock_tools.subprocess.run.assert_not_called()
    mock_tools.download.file.assert_not_called()


def test_installs_android_emulator(mock_tools, android_sdk):
    """The emulator tools will be installed if needed."""
    android_sdk.verify_emulator()

    # Platforms folder now exists
    assert (android_sdk.root_path / "platforms").exists()

    mock_tools.subprocess.run.assert_called_once_with(
        [
            os.fsdecode(android_sdk.sdkmanager_path),
            "platform-tools",
            "emulator",
        ],
        env=android_sdk.env,
        check=True,
    )


def test_partial_android_emulator_install(mock_tools, android_sdk):
    """If the Android emulator is only partially installed, it's not
    detected."""
    # Create the emulator *directory*, but not the actual binary.
    (android_sdk.root_path / "emulator").mkdir(parents=True)

    android_sdk.verify_emulator()

    # Platforms folder now exists
    assert (android_sdk.root_path / "platforms").exists()

    mock_tools.subprocess.run.assert_called_once_with(
        [
            os.fsdecode(android_sdk.sdkmanager_path),
            "platform-tools",
            "emulator",
        ],
        env=android_sdk.env,
        check=True,
    )


def test_install_problems_are_reported(mock_tools, android_sdk):
    """If the sdkmanager fails to properly install the Android emulator, an
    exception is raised."""
    # Configure `subprocess` module to crash as though it were a sad sdkmanager.
    mock_tools.subprocess.run.side_effect = subprocess.CalledProcessError(
        returncode=1,
        cmd=["ignored"],
    )
    with pytest.raises(BriefcaseCommandError):
        android_sdk.verify_emulator()
