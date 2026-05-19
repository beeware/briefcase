from unittest.mock import MagicMock

import pytest

from briefcase.integrations.android_sdk import AndroidSDK
from briefcase.integrations.base import ToolCache


@pytest.fixture
def mock_tools(tmp_path, mock_tools) -> ToolCache:
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
    # Mock available system images
    android_sdk.list_available_system_images = MagicMock(
        return_value=[
            "system-images;android-31;default;x86_64",
            "system-images;android-34;default;x86_64",
            "system-images;android-34;google_apis;x86_64",
            "system-images;android-31;default;arm64-v8a",
            "system-images;android-34;default;arm64-v8a",
            "system-images;android-34;google_apis;arm64-v8a",
            "system-images;android-CANARY;google_apis;x86_64",
            "system-images;android-CinnamonBun;google_apis_playstore;x86_64",
        ]
    )
    return android_sdk


@pytest.mark.parametrize(
    ("host_os", "host_arch", "emulator_abi"),
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

    # Mock the user providing several invalid names before getting it right.
    mock_tools.console.values = [
        "runningEmulator",  # an existing emulator
        "invalid name",  # A name with a space
        "annoying!",  # a name with non-alpha characters
        "new-emulator",  # A valid name!
        "2",  # Android version selection
        "1",  # image type selection
    ]

    # Mock the initial output of an AVD config file.
    avd_config_path = tmp_path / "home/.android/avd/new-emulator.avd/config.ini"
    avd_config_path.parent.mkdir(parents=True)
    with avd_config_path.open("w", encoding="utf-8") as f:
        f.write("hw.device.name=pixel\n")

    # Mock the internal emulator creation method
    android_sdk._create_emulator = MagicMock()

    # Create a mock app
    app = MagicMock()
    del app.min_os_version  # ensure getattr fallback is used

    # Create the emulator
    avd = android_sdk.create_emulator(app)

    # The expected device AVD was created.
    assert avd == "new-emulator"

    # The call was made to create the emulator
    android_sdk._create_emulator.assert_called_once_with(
        avd="new-emulator",
        device_type="pixel",
        skin="pixel_7_pro",
        system_image=f"system-images;android-34;default;{emulator_abi}",
    )


def test_default_name(mock_tools, android_sdk, tmp_path):
    """A new emulator can be created with the default name."""
    # This test doesn't validate most of the test process;
    # it only checks that the emulator is created with the default name.

    # User provides no input; default name, system image and image type will be used.
    mock_tools.console.values = [
        "",
        "",
        "",
    ]

    # Mock the internal emulator creation method
    android_sdk._create_emulator = MagicMock()

    # Create a mock app
    app = MagicMock()
    del app.min_os_version  # ensure getattr fallback is used

    # Create the emulator
    avd = android_sdk.create_emulator(app)

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
    # Default emulator name, default system image and default image type selection.
    mock_tools.console.values = [
        "",
        "",
        "",
    ]

    # Mock the internal emulator creation method
    android_sdk._create_emulator = MagicMock()

    # Create a mock app
    app = MagicMock()
    del app.min_os_version  # ensure getattr fallback is used

    # Create the emulator
    avd = android_sdk.create_emulator(app)

    # The expected device AVD was created.
    assert avd == "beePhone3"


def test_system_image_selection(mock_tools, android_sdk, tmp_path):
    """The user can select an Android version and image type."""
    mock_tools.console.values = [
        "",  # default emulator name
        "2",  # select version 34 (option 2 in the list)
        "2",  # select google_apis (option 2 in the list)
    ]

    # Mock the internal emulator creation method
    android_sdk._create_emulator = MagicMock()

    # Create a mock app
    app = MagicMock()
    del app.min_os_version  # ensure getattr fallback is used

    # Create the emulator
    avd = android_sdk.create_emulator(app)

    # The expected device AVD was created.
    assert avd == "beePhone"

    # The call was made to create the emulator
    android_sdk._create_emulator.assert_called_once_with(
        avd="beePhone",
        device_type="pixel",
        skin="pixel_7_pro",
        system_image="system-images;android-34;google_apis;x86_64",
    )
