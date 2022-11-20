import subprocess
from unittest.mock import MagicMock, patch

import pytest

from briefcase.exceptions import BriefcaseCommandError
from briefcase.integrations.android_sdk import AndroidSDK


@pytest.fixture
def android_sdk(android_sdk, tmp_path) -> AndroidSDK:
    android_sdk.tools.subprocess.check_output = MagicMock(
        return_value=(
            "  system-images;android-31;android-tv;arm64-v8a     | 3    | Android TV ARM 64 v8a System Image\n"
            "  system-images;android-31;android-tv;x86           | 3    | Android TV Intel x86 Atom System Image\n"
            "  system-images;android-31;default;arm64-v8a        | 4    | ARM 64 v8a System Image\n"
            "  system-images;android-31;default;x86_64           | 4    | Intel x86 Atom_64 System Image\n"
            "  system-images;android-31;google-tv;arm64-v8a      | 3    | Google TV ARM 64 v8a System Image\n"
            "  system-images;android-31;google-tv;x86            | 3    | Google TV Intel x86 Atom System Image\n"
            "  system-images;android-31;google_apis;arm64-v8a    | 10   | Google APIs ARM 64 v8a System Image\n"
            "  system-images;android-31;google_apis;x86_64       | 10   | Google APIs Intel x86 Atom_64 System Image\n"
            "  system-images;android-31;google_apis_playstore;arm64-v8a | Google Play ARM 64 v8a System Image\n"
            "  system-images;android-30;android-tv;arm64-v8a     | 3    | Android TV ARM 64 v8a System Image\n"
            "  system-images;android-30;android-tv;x86           | 3    | Android TV Intel x86 Atom System Image\n"
            "  system-images;android-30;default;arm64-v8a        | 4    | ARM 64 v8a System Image\n"
            "  system-images;android-30;default;x86_64           | 4    | Intel x86 Atom_64 System Image\n"
            "  system-images;android-30;google-tv;arm64-v8a      | 3    | Google TV ARM 64 v8a System Image\n"
            "  system-images;android-30;google-tv;x86            | 3    | Google TV Intel x86 Atom System Image\n"
            "  system-images;android-30;google_apis;arm64-v8a    | 10   | Google APIs ARM 64 v8a System Image\n"
            "  system-images;android-30;google_apis;x86_64       | 10   | Google APIs Intel x86 Atom_64 System Image\n"
            "  system-images;android-30;google_apis_playstore;arm64-v8a | Google Play ARM 64 v8a System Image\n"
        )
    )
    return android_sdk


def test_detect_system_images(android_sdk, mock_tools):
    mock_tools.input.values = ["1"]
    system_image = android_sdk.detect_system_images()
    assert system_image == "system-images;android-31;default;x86_64"
    assert len(mock_tools.input.prompts) == 1


@patch("briefcase.integrations.android_sdk.AndroidSDK.select_system_images")
def test_detect_system_images_obtain_new(
    mock_select_system_images, android_sdk, mock_tools
):
    mock_tools.input.values = ["3"]
    mock_select_system_images.return_value = "system-images;android-31;default;x86_64"
    system_image = android_sdk.detect_system_images()
    assert system_image == "system-images;android-31;default;x86_64"
    assert len(mock_tools.input.prompts) == 1


def test_detect_system_images_error(android_sdk, mock_tools):
    """If there is a problem retrieving the system image list, an error is
    returned."""
    mock_tools.subprocess.check_output.side_effect = subprocess.CalledProcessError(
        cmd="sdkmanager --list",
        returncode=None,
    )
    with pytest.raises(BriefcaseCommandError):
        android_sdk.detect_system_images()
