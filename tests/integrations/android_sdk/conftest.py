from pathlib import Path
from unittest.mock import MagicMock

import pytest

from briefcase.integrations.android_sdk import ADB, AndroidSDK
from briefcase.integrations.base import ToolCache
from briefcase.integrations.file import File
from briefcase.integrations.java import JDK
from briefcase.integrations.subprocess import Subprocess

# current versions of Android SDK Manager
SDK_MGR_VER = "19.0"
SDK_MGR_DL_VER = "13114758"

# SHA256 checksums for the command-line tools ZIP for SDK_MGR_DL_VER, keyed by
# the same "mac"/"linux"/"win" tag used in `_test_download_tag` fixtures across
# the AndroidSDK test suite.
CMDLINE_TOOLS_SHA256 = {
    "mac": "5673201e6f3869f418eeed3b5cb6c4be7401502bd0aae1b12a29d164d647a54e",
    "linux": "7ec965280a073311c339e571cd5de778b9975026cfcbe79f2b1cdcb1e15317ee",
    "win": "98b565cb657b012dae6794cefc0f66ae1efb4690c699b78a614b4a6a3505b003",
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
