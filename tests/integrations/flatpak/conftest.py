from unittest.mock import MagicMock

import pytest

from briefcase.integrations.base import ToolCache
from briefcase.integrations.download import Download
from briefcase.integrations.flatpak import Flatpak
from briefcase.integrations.subprocess import Subprocess


@pytest.fixture
def mock_tools(mock_tools) -> ToolCache:
    mock_tools.host_os = "Linux"
    mock_tools.host_arch = "gothic"

    # Mock default tools
    mock_tools.subprocess = MagicMock(spec_set=Subprocess)
    mock_tools.download = MagicMock(spec_set=Download)

    return mock_tools


@pytest.fixture
def flatpak(mock_tools):
    return Flatpak(tools=mock_tools)
