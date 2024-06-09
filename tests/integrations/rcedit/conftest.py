from unittest.mock import MagicMock

import pytest

from briefcase.integrations.base import ToolCache
from briefcase.integrations.file import File
from briefcase.integrations.rcedit import RCEdit
from briefcase.integrations.subprocess import Subprocess


@pytest.fixture
def mock_tools(tmp_path, mock_tools) -> ToolCache:
    mock_tools.host_os = "Windows"
    mock_tools.host_arch = "wonky"

    # Mock default tools
    mock_tools.subprocess = MagicMock(spec_set=Subprocess)
    mock_tools.file = MagicMock(spec_set=File)

    return mock_tools


@pytest.fixture
def rcedit(mock_tools) -> RCEdit:
    return RCEdit(mock_tools)
