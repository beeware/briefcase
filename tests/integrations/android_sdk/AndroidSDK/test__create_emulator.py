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
        ("Windows", "AMD64", "x86_64"),
        ("Linux", "x86_64", "x86_64"),
        ("Linux", "aarch64", "arm64-v8a"),
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

    # Mock system image and skin verification
    android_sdk.verify_system_image = MagicMock()
    android_sdk.verify_emulator_skin = MagicMock()

    # Mock the initial output of an AVD config file.
    avd_config_path = tmp_path / "home/.android/avd/new-emulator.avd/config.ini"
    avd_config_path.parent.mkdir(parents=True)
    with avd_config_path.open("w", encoding="utf-8") as f:
        f.write("hw.device.name=pixel\n")

    # Create the emulator
    android_sdk._create_emulator(
        avd="new-emulator",
        device_type="slab",
        skin="slab_skin",
        system_image="system-images;android-42;default;gothic",
    )

    # The system image was verified
    android_sdk.verify_system_image.assert_called_once_with(
        "system-images;android-42;default;gothic"
    )

    # The emulator skin was verified
    android_sdk.verify_emulator_skin.assert_called_once_with("slab_skin")

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
            "system-images;android-42;default;gothic",
            "--device",
            "slab",
        ],
        env=android_sdk.env,
    )

    # Emulator configuration file has been appended.
    with avd_config_path.open(encoding="utf-8") as f:
        config = f.read().split("\n")
    assert "hw.keyboard=yes" in config
    assert "skin.name=slab_skin" in config


@pytest.mark.parametrize(
    "host_os, host_arch, emulator_abi",
    [
        ("Darwin", "x86_64", "x86_64"),
        ("Darwin", "arm64", "arm64-v8a"),
        ("Windows", "AMD64", "x86_64"),
        ("Linux", "x86_64", "x86_64"),
        ("Linux", "aarch64", "arm64-v8a"),
    ],
)
def test_create_emulator_with_defaults(
    mock_tools,
    android_sdk,
    tmp_path,
    host_os,
    host_arch,
    emulator_abi,
):
    """A new emulator can be created using default properties."""
    # This test validates everything going well on first run.
    # This means the skin will be downloaded and unpacked.

    # Mock the hardware and operating system to specific values
    mock_tools.host_os = host_os
    mock_tools.host_arch = host_arch

    # Mock system image and skin verification
    android_sdk.verify_system_image = MagicMock()
    android_sdk.verify_emulator_skin = MagicMock()

    # Mock the initial output of an AVD config file.
    avd_config_path = tmp_path / "home/.android/avd/new-emulator.avd/config.ini"
    avd_config_path.parent.mkdir(parents=True)
    with avd_config_path.open("w", encoding="utf-8") as f:
        f.write("hw.device.name=pixel\n")

    # Create the emulator using defaults
    android_sdk._create_emulator(avd="new-emulator")

    # The system image was verified
    android_sdk.verify_system_image.assert_called_once_with(
        f"system-images;android-31;default;{emulator_abi}"
    )

    # The emulator skin was verified
    android_sdk.verify_emulator_skin.assert_called_once_with("pixel_7_pro")

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
    )

    # Emulator configuration file has been appended.
    with avd_config_path.open(encoding="utf-8") as f:
        config = f.read().split("\n")
    assert "hw.keyboard=yes" in config
    assert "skin.name=pixel_7_pro" in config


def test_create_failure(mock_tools, android_sdk):
    """If avdmanager fails, an error is raised."""
    # Mock system image and skin verification
    android_sdk.verify_system_image = MagicMock()
    android_sdk.verify_emulator_skin = MagicMock()

    # Mock an avdmanager failure.
    mock_tools.subprocess.check_output.side_effect = subprocess.CalledProcessError(
        returncode=1, cmd="avdmanager"
    )

    # Create the emulator
    with pytest.raises(BriefcaseCommandError):
        android_sdk._create_emulator(avd="new-emulator")

    # The system image was verified
    android_sdk.verify_system_image.assert_called_once_with(ANY)

    # The emulator skin was verified
    android_sdk.verify_emulator_skin.assert_called_once_with("pixel_7_pro")

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
    )


def test_default_name(mock_tools, android_sdk, tmp_path):
    """A new emulator can be created with the default name."""
    # This test doesn't validate most of the test process;
    # it only checks that the emulator is created with the default name.

    # User provides no input; default name will be used
    mock_tools.input.return_value = ""

    # Mock the initial output of an AVD config file.
    avd_config_path = tmp_path / "home/.android/avd/beePhone.avd/config.ini"
    avd_config_path.parent.mkdir(parents=True)
    with avd_config_path.open("w", encoding="utf-8") as f:
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
    avd_config_path = tmp_path / "home/.android/avd/beePhone3.avd/config.ini"
    avd_config_path.parent.mkdir(parents=True)
    with avd_config_path.open("w", encoding="utf-8") as f:
        f.write("hw.device.name=pixel\n")

    # Create the emulator
    avd = android_sdk.create_emulator()

    # The expected device AVD was created.
    assert avd == "beePhone3"
