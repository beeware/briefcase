import os
from unittest.mock import MagicMock

import pytest

from briefcase.integrations.base import ToolCache
from briefcase.integrations.file import File
from briefcase.integrations.subprocess import Subprocess

WIX_DOWNLOAD_URL = (
    "https://github.com/wixtoolset/wix/releases/download/v5.0.2/wix-cli-x64.msi"
)
WIX_EXE_PATH = "PFiles64/WiX Toolset v5.0/bin/wix.exe"
WIX_UI_PATH = (
    "CFiles64/WixToolset/extensions/WixToolset.UI.wixext/5.0.2/wixext5/"
    "WixToolset.UI.wixext.dll"
)


@pytest.fixture
def mock_tools(tmp_path, mock_tools) -> ToolCache:
    mock_tools.host_os = "Windows"
    mock_tools.os = MagicMock(spec=os)

    # Mock default tools
    mock_tools.subprocess = MagicMock(spec_set=Subprocess)
    mock_tools.file.download = MagicMock(spec_set=File.download)

    return mock_tools


@pytest.fixture
def wix_path(tmp_path):
    return tmp_path / "tools/wix"
