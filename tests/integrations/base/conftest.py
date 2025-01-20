import pytest

from briefcase.console import Console
from briefcase.integrations.base import ToolCache


@pytest.fixture
def simple_tools(tmp_path):
    return ToolCache(console=Console(), base_path=tmp_path)
