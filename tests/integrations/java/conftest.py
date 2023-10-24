from unittest.mock import MagicMock

import pytest

from briefcase.integrations.base import ToolCache
from briefcase.integrations.download import Download
from briefcase.integrations.subprocess import Subprocess

JDK_RELEASE = "17.0.9"
JDK_BUILD = "9"


@pytest.fixture
def mock_tools(mock_tools, tmp_path) -> ToolCache:
    # Mock default tools
    mock_tools.subprocess = MagicMock(spec_set=Subprocess)
    mock_tools.download = MagicMock(spec_set=Download)

    return mock_tools
