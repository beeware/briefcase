import os
from unittest.mock import MagicMock

import pytest

from briefcase.integrations.base import ToolCache
from briefcase.integrations.subprocess import Subprocess


@pytest.fixture
def mock_tools(tmp_path, mock_tools) -> ToolCache:
    mock_tools.host_os = "Windows"

    mock_tools.os.environ = {
        "ProgramFiles(x86)": os.fsdecode(tmp_path / "Program Files (x86)")
    }

    mock_tools.subprocess = Subprocess(mock_tools)
    mock_tools.subprocess.check_output = MagicMock()

    return mock_tools
