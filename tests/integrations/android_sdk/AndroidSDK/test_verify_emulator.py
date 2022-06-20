import os
import subprocess
from pathlib import Path

import pytest

from briefcase.exceptions import BriefcaseCommandError


def test_succeeds_immediately_if_emulator_installed(mock_sdk):
    """`verify_emulator()` exits early if the emulator exists in its
    root_path."""
    # Create `emulator` within `root_path`.
    (mock_sdk.root_path / "emulator").mkdir(parents=True)

    mock_sdk.verify_emulator()

    # No extra calls made
    mock_sdk.command.subprocess.run.assert_not_called()
    mock_sdk.command.requests.get.assert_not_called()


def test_succeeds_immediately_if_emulator_installed_with_debug(mock_sdk, tmp_path):
    """If the emulator exists and debug is turned on, the list of packages is
    displayed."""
    # Turn up logging to debug levels
    mock_sdk.command.logger.verbosity = 2

    # Create `emulator` within `root_path`.
    (mock_sdk.root_path / "emulator").mkdir(parents=True)

    mock_sdk.verify_emulator()

    # No extra calls made
    mock_sdk.command.requests.get.assert_not_called()

    # But a call to run is made to dump the installed packages
    mock_sdk.command.subprocess.run.assert_called_once_with(
        [os.fsdecode(mock_sdk.sdkmanager_path), "--list_installed"],
        env={
            "ANDROID_SDK_ROOT": os.fsdecode(tmp_path / "sdk"),
            "JAVA_HOME": os.fsdecode(Path("/path/to/jdk")),
        },
        check=True,
    )


def test_installs_android_emulator(mock_sdk):
    """The emulator tools will be installed if needed."""
    mock_sdk.verify_emulator()

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
