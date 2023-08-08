from pathlib import Path
from unittest.mock import MagicMock

import pytest

from briefcase.integrations.android_sdk import ADB, AndroidSDK
from briefcase.integrations.base import ToolCache
from briefcase.integrations.download import Download
from briefcase.integrations.java import JDK
from briefcase.integrations.subprocess import Subprocess

# current versions of Android SDK Manager
SDK_MGR_VER = "9.0"
SDK_MGR_DL_VER = "9477386"


@pytest.fixture
def mock_tools(mock_tools, tmp_path) -> ToolCache:
    # Mock default tools
    mock_tools.subprocess = MagicMock(spec_set=Subprocess)
    mock_tools.download = MagicMock(spec_set=Download)

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
