from unittest.mock import MagicMock

import pytest

from briefcase.integrations.base import ToolCache
from briefcase.integrations.subprocess import Subprocess


@pytest.fixture
def mock_tools(tmp_path, mock_tools) -> ToolCache:
    mock_tools.subprocess = MagicMock(spec_set=Subprocess)

    return mock_tools


def test_detect_system_images(mock_tools):
    system_images = (
        "  system-images;android-31;android-tv;arm64-v8a            | 3  | Android TV ARM 64 v8a System Image\n"
        "  system-images;android-31;android-tv;x86                  | 3  | Android TV Intel x86 Atom System Image\n"
        "  system-images;android-31;default;arm64-v8a               | 4  | ARM 64 v8a System Image\n"
        "  system-images;android-31;default;x86_64                  | 4  | Intel x86 Atom_64 System Image\n"
        "  system-images;android-31;google-tv;arm64-v8a             | 3  | Google TV ARM 64 v8a System Image\n"
        "  system-images;android-31;google-tv;x86                   | 3  | Google TV Intel x86 Atom System Image\n"
        "  system-images;android-31;google_apis;arm64-v8a           | 10 | Google APIs ARM 64 v8a System Image\n"
        "  system-images;android-31;google_apis;x86_64            | 10 | Google APIs Intel x86 Atom_64 System Image\n"
        "  system-images;android-31;google_apis_playstore;arm64-v8a | 9  | Google Play ARM 64 v8a System Image\n"
    )

    mock_tools.subprocess.check_output.return_value = system_images

    select_option = MagicMock()
    select_option.return_value = "system-images;android-26;default;x86_64"
    system_image = select_option.return_value

    assert system_image == "system-images;android-26;default;x86_64"
