from pathlib import Path
from unittest.mock import MagicMock

import pytest

from briefcase.config import AppConfig
from briefcase.console import Console
from briefcase.integrations.base import ToolCache


class DummyApp(AppConfig):
    def __init__(self):
        super().__init__(
            app_name="dummy",
            formal_name="Dummy App",
            bundle="com.example",
            version="1.0",
            base_path=Path.cwd(),
        )


@pytest.fixture
def dummy_console():
    return MagicMock(spec_set=Console)


@pytest.fixture
def dummy_tools(tmp_path) -> ToolCache:
    tools = MagicMock(spec_set=ToolCache)
    tools.base_path = tmp_path
    tools.home_path = tmp_path
    tools.console = MagicMock(spec_set=Console)
    tools.host_os = "Linux"  # or whatever makes sense for your use
    tools.os.environ = {}
    return tools


@pytest.fixture
def dummy_app():
    return DummyApp()
