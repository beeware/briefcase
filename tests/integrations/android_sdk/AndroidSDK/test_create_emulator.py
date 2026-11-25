from unittest.mock import MagicMock, call

import pytest

from briefcase.exceptions import BriefcaseCommandError
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
        "2",  # Android API level selection (android-34)
        "1",  # image type selection (default)
        "",  # default device type
        "runningEmulator",  # an existing emulator
        "invalid name",  # A name with a space
        "annoying!",  # a name with non-alpha characters
        "new-emulator",  # A valid name!
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
        device_type="pixel_7",
        skin="pixel_7",
        system_image=f"system-images;android-34;default;{emulator_abi}",
    )


def test_default_name(mock_tools, android_sdk, tmp_path):
    """A new emulator can be created with the default name."""
    # This test doesn't validate most of the test process;
    # it only checks that the emulator is created with the default name.

    # User provides no input; default name, system image and image type will be used
    mock_tools.console.values = ["", "", "", ""]

    # Mock the internal emulator creation method
    android_sdk._create_emulator = MagicMock()

    # Create a mock app
    app = MagicMock()
    del app.min_os_version  # ensure getattr fallback is used

    # Create the emulator
    avd = android_sdk.create_emulator(app)

    # The expected device AVD was created.
    assert avd == "beePhone-31"


def test_default_name_with_collisions(mock_tools, android_sdk, tmp_path):
    """The default name will avoid collisions with existing emulators."""
    # This test doesn't validate most of the test process;
    # it only checks that the emulator is created with the default name.

    # Create some existing emulators that will collide with the default name.
    android_sdk.emulators = MagicMock(
        return_value=[
            "beePhone-31-2",
            "runningEmulator",
            "beePhone-35",
            "beePhone-31",
            "beePhone",
        ]
    )
    # Default emulator name, default system image and default image type selection.
    mock_tools.console.values = ["", "", "", ""]

    # Mock the internal emulator creation method
    android_sdk._create_emulator = MagicMock()

    # Create a mock app
    app = MagicMock()
    del app.min_os_version  # ensure getattr fallback is used

    # Create the emulator
    avd = android_sdk.create_emulator(app)

    # The expected device AVD was created.
    assert avd == "beePhone-31-3"


@pytest.fixture
def mock_selection_question(mock_tools):
    mock_tools.console.selection_question = (mock := MagicMock())
    return mock


@pytest.mark.parametrize(
    ("available_images", "options", "default"),
    [
        # API levels appear in numerical order, and only once each.
        # The default API level is used if it's present, even if it isn't the lowest.
        (
            [
                "system-images;android-30;google_apis;x86_64",
                "system-images;android-31;default;x86_64",
                "system-images;android-32;google_apis;x86_64",
                "system-images;android-30;default;x86_64",
            ],
            ["android-30", "android-31", "android-32"],
            "android-31",
        ),
        # Minor version numbers are sorted correctly.
        # When the default API level isn't present, the lowest version is the default.
        (
            [
                "system-images;android-31.10;default;x86_64",
                "system-images;android-31.11;default;x86_64",
                "system-images;android-31.1;default;x86_64",
                "system-images;android-31.2;default;x86_64",
            ],
            ["android-31.1", "android-31.2", "android-31.10", "android-31.11"],
            "android-31.1",
        ),
    ],
)
def test_api_level_selection(
    mock_tools,
    mock_selection_question,
    android_sdk,
    available_images,
    options,
    default,
):
    android_sdk.list_available_system_images = MagicMock(return_value=available_images)
    mock_tools.console.values = [""]  # default emulator name
    mock_selection_question.side_effect = [default, "default", "small_phone"]
    android_sdk._create_emulator = MagicMock()

    android_sdk.create_emulator(MagicMock())
    assert mock_selection_question.mock_calls == [
        call(
            intro="Select the API level for the emulator:",
            description="API level",
            options=options,
            default=default,
        ),
        call(
            intro="Select the system image type:",
            description="Image type",
            options=["default"],
            default="default",
        ),
        call(
            intro="What type of device would you like to emulate?",
            description="Device Type",
            options=android_sdk.device_types,
            default=android_sdk.DEFAULT_DEVICE_TYPE,
        ),
    ]


@pytest.mark.parametrize(
    ("available_images", "options", "default"),
    [
        # Image types are shown in alphabetical order.
        # The default type is "default", then "google_apis", then "google_apis_ps16k".
        (
            [
                "system-images;android-31;google_apis;x86_64",
                "system-images;android-31;default;x86_64",
                "system-images;android-31;google_apis_ps16k;x86_64",
                "system-images;android-31;extra;x86_64",
            ],
            ["default", "extra", "google_apis", "google_apis_ps16k"],
            "default",
        ),
        (
            [
                "system-images;android-31;google_apis_ps16k;x86_64",
                "system-images;android-31;google_apis;x86_64",
                "system-images;android-31;extra;x86_64",
            ],
            ["extra", "google_apis", "google_apis_ps16k"],
            "google_apis",
        ),
        (
            [
                "system-images;android-31;google_apis_ps16k;x86_64",
                "system-images;android-31;extra;x86_64",
            ],
            ["extra", "google_apis_ps16k"],
            "google_apis_ps16k",
        ),
        (
            [
                "system-images;android-31;extra;x86_64",
            ],
            ["extra"],
            None,
        ),
    ],
)
def test_image_type_selection(
    mock_tools,
    mock_selection_question,
    android_sdk,
    available_images,
    options,
    default,
):
    android_sdk.list_available_system_images = MagicMock(return_value=available_images)
    mock_tools.console.values = [""]  # default emulator name
    mock_selection_question.side_effect = ["android-31", default, "small_phone"]
    android_sdk._create_emulator = MagicMock()

    android_sdk.create_emulator(MagicMock())
    assert mock_selection_question.mock_calls == [
        call(
            intro="Select the API level for the emulator:",
            description="API level",
            options=["android-31"],
            default="android-31",
        ),
        call(
            intro="Select the system image type:",
            description="Image type",
            options=options,
            default=default,
        ),
        call(
            intro="What type of device would you like to emulate?",
            description="Device Type",
            options=android_sdk.device_types,
            default=android_sdk.DEFAULT_DEVICE_TYPE,
        ),
    ]


def test_system_image_selection(mock_tools, android_sdk, tmp_path):
    """The user can select an Android version and image type."""
    mock_tools.console.values = [
        "2",  # select API level 34 (option 2 in the list)
        "2",  # image type selection (google_apis option 2 in the list)
        "",  # default image type
        "",  # default emulator name
    ]

    # Mock the internal emulator creation method
    android_sdk._create_emulator = MagicMock()

    # Create a mock app
    app = MagicMock()
    del app.min_os_version  # ensure getattr fallback is used

    # Create the emulator
    avd = android_sdk.create_emulator(app)

    # The expected device AVD was created.
    assert avd == "beePhone-34"

    # The call was made to create the emulator
    android_sdk._create_emulator.assert_called_once_with(
        avd="beePhone-34",
        device_type="pixel_7",
        skin="pixel_7",
        system_image="system-images;android-34;google_apis;x86_64",
    )


def test_no_available_system_images(mock_tools, android_sdk, tmp_path):
    """If no system images are available, an error is raised."""
    android_sdk.list_available_system_images = MagicMock(return_value=[])

    # User provides a name before the error is raised
    mock_tools.console.values = [""]  # default emulator name

    # Create a mock app
    app = MagicMock()
    del app.min_os_version  # ensure getattr fallback is used

    # No system image detected
    with pytest.raises(BriefcaseCommandError):
        android_sdk.create_emulator(app)


def test_create_emulator_with_min_os_version(mock_tools, android_sdk, tmp_path):
    """create_emulator passes app's min_os_version to list_available_system_images."""
    mock_tools.console.values = [
        "2",  # API level selection (android-34)
        "1",  # image type selection (default)
        "",  # Device type
        "new-emulator",  # emulator name
    ]
    # Mock the initial output of an AVD config file.
    avd_config_path = tmp_path / "home/.android/avd/new-emulator.avd/config.ini"
    avd_config_path.parent.mkdir(parents=True)
    with avd_config_path.open("w", encoding="utf-8") as f:
        f.write("hw.device.name=pixel\n")
    # Mock the internal emulator creation method
    android_sdk._create_emulator = MagicMock()
    # Create a mock app with min_os_version explicitly set
    app = MagicMock()
    app.min_os_version = 28
    # Create the emulator
    android_sdk.create_emulator(app)
    # Verify list_available_system_images was called with the app's min_os_version
    android_sdk.list_available_system_images.assert_called_once_with(min_api_level=28)


def test_custom_device_type(mock_tools, android_sdk, tmp_path):
    """A custom device type can be created with the default name."""
    # This test doesn't validate most of the test process;
    # it only checks that the emulator is created with the default name.

    mock_tools.console.values = [
        "",  # Default API level
        "",  # Default image type
        "12",  # Option 12: Pixel 9 Pro XL.
        "",  # Accept default name
    ]

    # Mock the internal emulator creation method
    android_sdk._create_emulator = MagicMock()

    # Create a mock app
    app = MagicMock()

    # Create the emulator
    avd = android_sdk.create_emulator(app)

    # The expected device AVD was created.
    assert avd == "beePhone-31"

    # The call was made to create the emulator
    android_sdk._create_emulator.assert_called_once_with(
        avd="beePhone-31",
        device_type="pixel_9_pro_xl",
        skin="pixel_9_pro_xl",
        system_image="system-images;android-31;default;x86_64",
    )
