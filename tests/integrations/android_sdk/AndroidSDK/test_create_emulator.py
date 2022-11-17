from unittest.mock import MagicMock

import pytest

from briefcase.console import Console
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

    # Mock the initial output of an AVD config file.
    avd_config_path = (
        tmp_path / "home" / ".android" / "avd" / "new-emulator.avd" / "config.ini"
    )
    avd_config_path.parent.mkdir(parents=True)
    with avd_config_path.open("w") as f:
        f.write("hw.device.name=pixel\n")

    # Mock the internal emulator creation methdo
    android_sdk._create_emulator = MagicMock()

    # Create the emulator
    avd = android_sdk.create_emulator()

    # The expected device AVD was created.
    assert avd == "new-emulator"

    # The call was made to create the emulator
    android_sdk._create_emulator.assert_called_once_with(
        avd="new-emulator",
        device_type="pixel",
        skin="pixel_3a",
        system_image=f"system-images;android-31;default;{emulator_abi}",
    )


def test_default_name(mock_tools, android_sdk, tmp_path):
    """A new emulator can be created with the default name."""
    # This test doesn't validate most of the test process;
    # it only checks that the emulator is created with the default name.

    # User provides no input; default name will be used
    mock_tools.input.return_value = ""

    # Mock the internal emulator creation methdo
    android_sdk._create_emulator = MagicMock()

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

    # Mock the internal emulator creation methdo
    android_sdk._create_emulator = MagicMock()

    # Create the emulator
    avd = android_sdk.create_emulator()

    # The expected device AVD was created.
    assert avd == "beePhone3"
