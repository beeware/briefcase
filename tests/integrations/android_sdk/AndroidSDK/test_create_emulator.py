import os
import subprocess
from unittest.mock import ANY, MagicMock

import pytest

from briefcase.console import Console
from briefcase.exceptions import BriefcaseCommandError
from briefcase.integrations.android_sdk import AndroidSDK
from briefcase.integrations.base import ToolCache


@pytest.fixture
def mock_tools(tmp_path, mock_tools) -> ToolCache:
    mock_tools.input = MagicMock(spec_set=Console)

    # For default test purposes, assume we're on macOS x86_64
    mock_tools.host_os = "Darwin"
    mock_tools.host_arch = "x86_64"

    return mock_tools


@pytest.fixture
def android_sdk(android_sdk) -> AndroidSDK:
    # Mock some existing emulators
    android_sdk.emulators = MagicMock(
        return_value=[
            "runningEmulator",
            "idleEmulator",
        ]
    )
    return android_sdk


@pytest.mark.parametrize(
    "host_os, host_arch, emulator_abi",
    [
        ("Darwin", "x86_64", "x86_64"),
        ("Darwin", "arm64", "arm64-v8a"),
        ("Windows", "x86_64", "x86_64"),
        ("Linux", "x86_64", "x86_64"),
    ],
)
def test_create_emulator(
    mock_tools,
    android_sdk,
    tmp_path,
    host_os,
    host_arch,
    emulator_abi,
):
    """A new emulator can be created."""
    # This test validates everything going well on first run.
    # This means the skin will be downloaded and unpacked.

    # Mock the hardware and operating system to specific values
    mock_tools.host_os = host_os
    mock_tools.host_arch = host_arch

    # Mock the user providing several invalid names before getting it right.
    mock_tools.input.side_effect = [
        "runningEmulator",
        "invalid name",
        "annoying!",
        "new-emulator",
    ]

    # Mock system image and skin verification
    android_sdk.verify_system_image = MagicMock()
    android_sdk.verify_emulator_skin = MagicMock()

    # Mock the initial output of an AVD config file.
    avd_config_path = (
        tmp_path / "home" / ".android" / "avd" / "new-emulator.avd" / "config.ini"
    )
    avd_config_path.parent.mkdir(parents=True)
    with avd_config_path.open("w") as f:
        f.write("hw.device.name=pixel\n")

    # Create the emulator
    avd = android_sdk.create_emulator()

    # The expected device AVD was created.
    assert avd == "new-emulator"

    # The system image was verified
    android_sdk.verify_system_image.assert_called_once_with(
        f"system-images;android-31;default;{emulator_abi}"
    )

    # The emulator skin was verified
    android_sdk.verify_emulator_skin.assert_called_once_with("pixel_3a")

    # avdmanager was invoked
    mock_tools.subprocess.check_output.assert_called_once_with(
        [
            os.fsdecode(android_sdk.avdmanager_path),
            "--verbose",
            "create",
            "avd",
            "--name",
            "new-emulator",
            "--abi",
            emulator_abi,
            "--package",
            f"system-images;android-31;default;{emulator_abi}",
            "--device",
            "pixel",
        ],
        env=android_sdk.env,
        stderr=subprocess.STDOUT,
    )

    # Emulator configuration file has been appended.
    with avd_config_path.open() as f:
        config = f.read().split("\n")
    assert "hw.keyboard=yes" in config
    assert "skin.name=pixel_3a" in config


def test_create_failure(mock_tools, android_sdk):
    """If avdmanager fails, an error is raised."""
    # Mock the user getting a valid name first time
    mock_tools.input.return_value = "new-emulator"

    # Mock system image and skin verification
    android_sdk.verify_system_image = MagicMock()
    android_sdk.verify_emulator_skin = MagicMock()

    # Mock an avdmanager failure.
    mock_tools.subprocess.check_output.side_effect = subprocess.CalledProcessError(
        returncode=1, cmd="avdmanager"
    )

    # Create the emulator
    with pytest.raises(BriefcaseCommandError):
        android_sdk.create_emulator()

    # The system image was verified
    android_sdk.verify_system_image.assert_called_once_with(ANY)

    # The emulator skin was verified
    android_sdk.verify_emulator_skin.assert_called_once_with("pixel_3a")

    # avdmanager was invoked
    mock_tools.subprocess.check_output.assert_called_once_with(
        [
            os.fsdecode(android_sdk.avdmanager_path),
            "--verbose",
            "create",
            "avd",
            "--name",
            "new-emulator",
            "--abi",
            "x86_64",
            "--package",
            "system-images;android-31;default;x86_64",
            "--device",
            "pixel",
        ],
        env=android_sdk.env,
        stderr=subprocess.STDOUT,
    )


def test_default_name(mock_tools, android_sdk, tmp_path):
    """A new emulator can be created with the default name."""
    # This test doesn't validate most of the test process;
    # it only checks that the emulator is created with the default name.

    # User provides no input; default name will be used
    mock_tools.input.return_value = ""

    # Mock the initial output of an AVD config file.
    avd_config_path = (
        tmp_path / "home" / ".android" / "avd" / "beePhone.avd" / "config.ini"
    )
    avd_config_path.parent.mkdir(parents=True)
    with avd_config_path.open("w") as f:
        f.write("hw.device.name=pixel\n")

    # Create the emulator
    avd = android_sdk.create_emulator()

    # The expected device AVD was created.
    assert avd == "beePhone"


def test_default_name_with_collisions(mock_tools, android_sdk, tmp_path):
    """The default name will avoid collisions with existing emulators."""
    # This test doesn't validate most of the test process;
    # it only checks that the emulator is created with the default name.

    # Create some existing emulators that will collide with the default name.
    android_sdk.emulators = MagicMock(
        return_value=[
            "beePhone2",
            "runningEmulator",
            "beePhone",
        ]
    )
    # User provides no input; default name will be used
    mock_tools.input.return_value = ""

    # Mock the initial output of an AVD config file.
    avd_config_path = (
        tmp_path / "home" / ".android" / "avd" / "beePhone3.avd" / "config.ini"
    )
    avd_config_path.parent.mkdir(parents=True)
    with avd_config_path.open("w") as f:
        f.write("hw.device.name=pixel\n")

    # Create the emulator
    avd = android_sdk.create_emulator()

    # The expected device AVD was created.
    assert avd == "beePhone3"
