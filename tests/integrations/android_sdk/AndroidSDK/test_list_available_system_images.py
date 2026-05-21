import subprocess

import pytest

from briefcase.exceptions import BriefcaseCommandError


def test_list_available_system_images(mock_tools, android_sdk):
    """Returns a sorted list of available system image package identifiers."""
    mock_tools.subprocess.check_output.return_value = (
        "Available Packages:\n"
        "  Path                                        | Version | Description\n"
        "  -------                                     | ------- | -------\n"
        "  system-images;android-34;default;x86_64     | 7       | Intel x86_64 Atom System Image\n"
        "  system-images;android-31;default;x86_64     | 5       | Intel x86_64 Atom System Image\n"
        "  system-images;android-25;default;x86_64     | 3       | Intel x86_64 Atom System Image\n"
        "  emulator                                    | 35.4.9  | Android Emulator\n"
    )

    result = android_sdk.list_available_system_images()

    # android-25 is filtered out (below minimum version)
    assert result == [
        "system-images;android-31;default;x86_64",
        "system-images;android-34;default;x86_64",
    ]
    mock_tools.subprocess.check_output.assert_called_once_with(
        [android_sdk.sdkmanager_path, "--list"],
        env=android_sdk.env,
    )


def test_list_available_system_images_dotted_version(mock_tools, android_sdk):
    """System images with dotted versions (e.g. android-36.1) are included."""
    mock_tools.subprocess.check_output.return_value = (
        "Available Packages:\n"
        "  Path                                         | Version | Description\n"
        "  -------                                      | ------- | -------\n"
        "  system-images;android-36.1;default;x86_64    | 1       | Intel x86_64 Atom System Image\n"
        "  system-images;android-36.1;default;arm64-v8a | 1       | ARM64 System Image\n"
        "  emulator                                     | 35.4.9  | Android Emulator\n"
    )

    result = android_sdk.list_available_system_images()

    assert result == [
        "system-images;android-36.1;default;x86_64",
    ]


def test_list_available_system_images_dotted_version_below_minimum(
    mock_tools, android_sdk
):
    """System images with dotted versions below the minimum are filtered out."""
    mock_tools.subprocess.check_output.return_value = (
        "Available Packages:\n"
        "  Path                                        | Version | Description\n"
        "  -------                                     | ------- | -------\n"
        "  system-images;android-25.1;default;x86_64   | 1       | Intel x86_64 Atom System Image\n"
        "  system-images;android-31;default;x86_64     | 5       | Intel x86_64 Atom System Image\n"
        "  system-images;android-31;default;ARM64-v8a  | 5       | ARM64 System Image\n"
        "  emulator                                    | 35.4.9  | Android Emulator\n"
    )

    result = android_sdk.list_available_system_images()

    # android-25.1 is filtered out (below minimum version 26)
    assert result == [
        "system-images;android-31;default;x86_64",
    ]


def test_list_available_system_images_named_version(mock_tools, android_sdk):
    """System images with named versions (e.g. android-CANARY) are included."""
    mock_tools.subprocess.check_output.return_value = (
        "Available Packages:\n"
        "  Path                                               | Version    | Description\n"
        "  -------                                            | -------    | -------\n"
        "  system-images;android-CANARY;google_apis;x86_64    | 1       | Google APIs Intel x86_64\n"
        "  system-images;android-CANARY;google_apis;arm64-v8a | 1       | Google APIs ARM64\n"
        "  emulator                                           | 35.4.9  | Android Emulator\n"
    )

    result = android_sdk.list_available_system_images()

    assert result == [
        "system-images;android-CANARY;google_apis;x86_64",
    ]


def test_list_available_system_images_other_abi(mock_tools, android_sdk):
    """System images for other architectures are filtered out."""
    mock_tools.subprocess.check_output.return_value = (
        "Available Packages:\n"
        "  Path                                        | Version | Description\n"
        "  -------                                     | ------- | -------\n"
        "  system-images;android-34;default;x86_64     | 7       | Intel x86_64 Atom System Image\n"
        "  system-images;android-34;default;arm64-v8a  | 7       | ARM 64 v8a System Image\n"
        "  emulator                                    | 35.4.9  | Android Emulator\n"
    )

    result = android_sdk.list_available_system_images()

    # Only x86_64 images returned (default test ABI is x86_64)
    assert result == [
        "system-images;android-34;default;x86_64",
    ]


def test_list_available_system_images_duplicates(mock_tools, android_sdk):
    """Duplicate entries in sdkmanager output are deduplicated."""
    mock_tools.subprocess.check_output.return_value = (
        "Available Packages:\n"
        "  Path                                        | Version | Description\n"
        "  -------                                     | ------- | -------\n"
        "  system-images;android-31;default;x86_64     | 5       | Intel x86_64 Atom System Image\n"
        "  system-images;android-31;default;x86_64     | 5       | Intel x86_64 Atom System Image\n"
        "  emulator                                    | 35.4.9  | Android Emulator\n"
    )

    result = android_sdk.list_available_system_images()

    assert result == [
        "system-images;android-31;default;x86_64",
    ]


def test_no_available_system_images(mock_tools, android_sdk):
    """If no system images are available, an empty list is returned."""
    mock_tools.subprocess.check_output.return_value = (
        "Available Packages:\n"
        "  Path                                        | Version | Description\n"
        "  -------                                     | ------- | -------\n"
        "  emulator                                    | 35.4.9  | Android Emulator\n"
    )

    result = android_sdk.list_available_system_images()

    assert result == []


def test_list_available_system_images_failure(mock_tools, android_sdk):
    """If sdkmanager fails, an error is raised."""
    mock_tools.subprocess.check_output.side_effect = subprocess.CalledProcessError(
        1, ""
    )

    with pytest.raises(BriefcaseCommandError):
        android_sdk.list_available_system_images()


def test_list_available_system_images_malformed_package(mock_tools, android_sdk):
    """Malformed package entries in sdkmanager output are skipped."""
    mock_tools.subprocess.check_output.return_value = (
        "Available Packages:\n"
        "  Path                                        | Version | Description\n"
        "  -------                                     | ------- | -------\n"
        "  system-images;android-31;default;x86_64     | 5       | Intel x86_64 Atom System Image\n"
        "  system-images;android-34                    | 7       | Malformed entry\n"
        "  emulator                                    | 35.4.9  | Android Emulator\n"
    )

    result = android_sdk.list_available_system_images()

    # Malformed entry is skipped
    assert result == [
        "system-images;android-31;default;x86_64",
    ]
