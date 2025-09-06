from unittest.mock import MagicMock

import pytest

from briefcase.console import Console
from briefcase.integrations.base import ToolCache
from briefcase.integrations.virtual_environment import VenvContext


@pytest.fixture
def dummy_console():
    return MagicMock(spec_set=Console)


@pytest.fixture
def dummy_tools(mock_tools) -> ToolCache:
    """Override the mock_tools from parent conftest for virtual_environment tests."""
    mock_tools.host_os = "Linux"

    return mock_tools


@pytest.fixture
def venv_path(tmp_path):
    return tmp_path / "test_venv"


@pytest.fixture
def venv_context(dummy_tools, venv_path):
    return VenvContext(
        tools=dummy_tools,
        venv_path=venv_path,
    )
