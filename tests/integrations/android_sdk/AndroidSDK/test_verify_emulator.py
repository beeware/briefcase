import subprocess

import pytest

from briefcase.exceptions import BriefcaseCommandError


def test_succeeds_immediately_if_emulator_installed(mock_sdk):
    """`verify_emulator()` exits early if the emulator exists in its root_path."""
    # Create `emulator` within `root_path`.
    (mock_sdk.root_path / "emulator").mkdir(parents=True)

    mock_sdk.verify_emulator()

    # No extra calls made
    mock_sdk.command.subprocess.run.assert_not_called()
    mock_sdk.command.requests.get.assert_not_called()


def test_installs_android_emulator(mock_sdk):
    "The emulator tools will be installed if needed"
    mock_sdk.verify_emulator()

    mock_sdk.command.subprocess.run.assert_called_once_with(
        [
            str(mock_sdk.sdkmanager_path),
            "platforms;android-28",
            "system-images;android-28;default;x86",
            "emulator",
            "platform-tools",
        ],
        env=mock_sdk.env,
        check=True,
    )


def test_install_problems_are_reported(mock_sdk):
    "If the sdkmanager fails to properly install the Android emulator, an exception is raised."
    # Configure `subprocess` module to crash as though it were a sad sdkmanager.
    mock_sdk.command.subprocess.run.side_effect = subprocess.CalledProcessError(
        returncode=1,
        cmd=["ignored"],
    )
    with pytest.raises(BriefcaseCommandError):
        mock_sdk.verify_emulator()
