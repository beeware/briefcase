import os
import subprocess
from pathlib import Path

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


def test_succeeds_immediately_if_emulator_installed_with_debug(mock_sdk, tmp_path):
    """If the emulator exist and debug is turned on, the list of packages is displayed"""
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
            "ANDROID_SDK_ROOT": os.fsdecode(tmp_path / 'sdk'),
            "JAVA_HOME": os.fsdecode(Path("/path/to/jdk")),
        },
        check=True,
    )


@pytest.mark.parametrize(
    "host_os, host_arch, emulator_abi",
    [
        ("Darwin", "x86_64", "x86_64"),
        ("Darwin", "arm64", "arm64-v8a"),
        ("Windows", "x86_64", "x86_64"),
        ("Linux", "x86_64", "x86_64"),
    ]
)
def test_installs_android_emulator(mock_sdk, host_os, host_arch, emulator_abi):
    "The emulator tools will be installed if needed"
    # Mock the hardware and OS
    mock_sdk.command.host_os = host_os
    mock_sdk.command.host_arch = host_arch

    mock_sdk.verify_emulator()

    mock_sdk.command.subprocess.run.assert_called_once_with(
        [
            os.fsdecode(mock_sdk.sdkmanager_path),
            "platform-tools",
            "emulator",
            f"system-images;android-31;default;{emulator_abi}",
        ],
        env=mock_sdk.env,
        check=True,
    )


@pytest.mark.parametrize(
    "host_os, host_arch",
    [
        ("Windows", "arm64"),
        ("Linux", "arm64"),
    ]
)
def test_unsupported_emulator_platform(mock_sdk, host_os, host_arch):
    "If the platform isn't supported by the Android emulator, an error is raised"

    mock_sdk.command.host_os = host_os
    mock_sdk.command.host_arch = host_arch

    with pytest.raises(
        BriefcaseCommandError,
        match=f"The Android emulator does not currently support {host_os} {host_arch} hardware"
    ):
        mock_sdk.verify_emulator()

    mock_sdk.command.subprocess.run.assert_not_called()


def test_install_problems_are_reported(mock_sdk):
    "If the sdkmanager fails to properly install the Android emulator, an exception is raised."
    # Configure `subprocess` module to crash as though it were a sad sdkmanager.
    mock_sdk.command.subprocess.run.side_effect = subprocess.CalledProcessError(
        returncode=1,
        cmd=["ignored"],
    )
    with pytest.raises(BriefcaseCommandError):
        mock_sdk.verify_emulator()
