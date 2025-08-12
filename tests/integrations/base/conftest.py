import pytest

from briefcase.integrations.base import ToolCache


@pytest.fixture
def simple_tools(dummy_console, tmp_path):
    return ToolCache(console=dummy_console, base_path=tmp_path)
