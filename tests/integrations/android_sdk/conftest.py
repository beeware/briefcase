from pathlib import Path
from unittest.mock import MagicMock

import pytest

from briefcase.integrations.android_sdk import ADB, AndroidSDK
from briefcase.integrations.base import ToolCache
from briefcase.integrations.file import File
from briefcase.integrations.java import JDK
from briefcase.integrations.subprocess import Subprocess

# current versions of Android SDK Manager
SDK_MGR_VER = "21.0"
SDK_MGR_DL_VER = "15641748"

# SHA256 checksums for the command-line tools ZIP for SDK_MGR_DL_VER, keyed by
# the same "mac"/"linux"/"win" tag used in `_test_download_tag` fixtures across
# the AndroidSDK test suite.
CMDLINE_TOOLS_SHA256 = {
    "mac": "a2253766e128f6d4ff594d23857b67f52028a7e8773b2634dcc3d3e60d13b290",
    "linux": "a66d5ef0238fc0162e9c1446602ce0dd41702d4dd7a94d2ce42d12b7f80baf7e",
    "win": "f911b4f03fbee117e2d22edb5f51a5efeae4e8c8aa78bb6bd3de4862ae299da6",
}


@pytest.fixture
def mock_tools(mock_tools, tmp_path) -> ToolCache:
    # Mock default tools
    mock_tools.subprocess = MagicMock(spec_set=Subprocess)
    mock_tools.file.download = MagicMock(spec_set=File.download)

    # Set up a JDK
    mock_tools.java = MagicMock(spec=JDK)
    mock_tools.java.java_home = Path("/path/to/jdk")

    return mock_tools


@pytest.fixture
def android_sdk(mock_tools, tmp_path) -> AndroidSDK:
    # Ensure root directory for SDK exists
    sdk_root = tmp_path / "sdk"
    sdk_root.mkdir(parents=True)

    return AndroidSDK(mock_tools, root_path=sdk_root)


@pytest.fixture
def adb(mock_tools) -> ADB:
    return ADB(mock_tools, "exampleDevice")
