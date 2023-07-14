import shutil
from unittest.mock import MagicMock

import pytest

from briefcase.integrations.base import ToolCache
from briefcase.integrations.download import Download
from briefcase.integrations.linuxdeploy import LinuxDeploy
from briefcase.integrations.subprocess import Subprocess


@pytest.fixture
def mock_tools(tmp_path, mock_tools) -> ToolCache:
    mock_tools.host_os = "Linux"
    mock_tools.host_arch = "i686"

    # Mock default tools
    mock_tools.subprocess = MagicMock(spec_set=Subprocess)
    mock_tools.download = MagicMock(spec_set=Download)

    # Restore shutil
    mock_tools.shutil = shutil

    # Create a dummy bundle path
    (tmp_path / "bundle").mkdir()

    return mock_tools


@pytest.fixture
def linuxdeploy(mock_tools):
    return LinuxDeploy(mock_tools)
