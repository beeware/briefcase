from unittest.mock import MagicMock

import pytest

from briefcase.integrations.base import ToolCache
from briefcase.integrations.flatpak import Flatpak
from briefcase.integrations.subprocess import Subprocess


@pytest.fixture
def mock_tools(mock_tools) -> ToolCache:
    mock_tools.subprocess = MagicMock(spec_set=Subprocess)
    return mock_tools


@pytest.fixture
def flatpak(mock_tools):
    mock_tools.host_arch = "gothic"
    return Flatpak(tools=mock_tools)
