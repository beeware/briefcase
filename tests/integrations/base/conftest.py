import pytest

from briefcase.console import Console, Log
from briefcase.integrations.base import ToolCache


@pytest.fixture
def simple_tools(tmp_path):
    return ToolCache(logger=Log(), console=Console(), base_path=tmp_path)
