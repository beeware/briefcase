import os
from subprocess import CalledProcessError

import pytest

from briefcase.exceptions import BriefcaseCommandError


@pytest.mark.parametrize(
    "host_os, host_arch",
    [
        ("Windows", "arm64"),
        ("Linux", "arm64"),
    ],
)
def test_unsupported_abi(mock_sdk, host_os, host_arch):
    """If the system has an unsupported ABI, raise an error."""
    # Mock the hardware and OS
    mock_sdk.command.host_os = host_os
    mock_sdk.command.host_arch = host_arch

    with pytest.raises(
        BriefcaseCommandError,
        match=f"The Android emulator does not currently support {host_os} {host_arch} hardware",
    ):
        mock_sdk.verify_system_image("system-images;android-31;default;x86_64")


@pytest.mark.parametrize(
    "bad_image_name",
    [
        # Patently invalid
        "cheesecake",
        # Only the prefix
        "system-images",
        # Not enough parts
        "system-images;android-31;default",
        # Broadly good structure, but bad initial prefix
        "system-image;android-31;default;anything",
    ],
)
def test_invalid_system_image(mock_sdk, bad_image_name):
    """If the system image name doesn't make sense, raise an error."""
    # Mock the host arch
    mock_sdk.command.host_arch = "x86_64"

    # Verify an system image that doesn't match the host architecture
    with pytest.raises(
        BriefcaseCommandError,
        match=rf"{bad_image_name!r} is not a valid system image name.",
    ):
        mock_sdk.verify_system_image(bad_image_name)


def test_incompatible_abi(mock_sdk, capsys):
    """If the system image doesn't match the emulator ABI, warn the user, but
    continue."""
    # Mock the host arch
    mock_sdk.command.host_arch = "x86_64"

    # Verify an system image that doesn't match the host architecture
    mock_sdk.verify_system_image("system-images;android-31;default;anything")

    # A warning message was output
    assert "WARNING: Unexpected emulator ABI" in capsys.readouterr().out

    # The system image was installed.
    mock_sdk.command.subprocess.run.assert_called_once_with(
        [
            os.fsdecode(mock_sdk.sdkmanager_path),
            "system-images;android-31;default;anything",
        ],
        env=mock_sdk.env,
        check=True,
    )


def test_existing_system_image(mock_sdk):
    """If the system image already exists, don't attempt to download it
    again."""
    # Mock the host arch
    mock_sdk.command.host_arch = "x86_64"

    # Mock the existence of a system image
    (mock_sdk.root_path / "system-images" / "android-31" / "default" / "x86_64").mkdir(
        parents=True
    )

    # Verify the system image that we already have
    mock_sdk.verify_system_image("system-images;android-31;default;x86_64")

    # sdkmanager was *not* called.
    mock_sdk.command.subprocess.run.assert_not_called()


def test_new_system_image(mock_sdk):
    """If the system image doesn't exist locally, it will be installed."""
    # Mock the host arch
    mock_sdk.command.host_arch = "x86_64"

    # Verify the system image, triggering a download
    mock_sdk.verify_system_image("system-images;android-31;default;x86_64")

    # The system image was installed.
    mock_sdk.command.subprocess.run.assert_called_once_with(
        [
            os.fsdecode(mock_sdk.sdkmanager_path),
            "system-images;android-31;default;x86_64",
        ],
        env=mock_sdk.env,
        check=True,
    )


def test_problem_downloading_system_image(mock_sdk):
    """If there is a failure downloading the system image, an error is
    raised."""
    # Mock the host arch
    mock_sdk.command.host_arch = "x86_64"

    # Mock a failure condition on subprocess.run
    mock_sdk.command.subprocess.run.side_effect = CalledProcessError(
        returncode=1, cmd="sdkmanager"
    )

    # Attempt to verify the system image
    with pytest.raises(
        BriefcaseCommandError,
        match="Error while installing the 'system-images;android-31;default;x86_64' Android system image.",
    ):
        mock_sdk.verify_system_image("system-images;android-31;default;x86_64")

    # An attempt to install the system image was made
    mock_sdk.command.subprocess.run.assert_called_once_with(
        [
            os.fsdecode(mock_sdk.sdkmanager_path),
            "system-images;android-31;default;x86_64",
        ],
        env=mock_sdk.env,
        check=True,
    )
