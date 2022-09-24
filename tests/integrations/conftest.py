import os
import platform
import shutil
import sys
from unittest.mock import MagicMock

import pytest

from briefcase.config import AppConfig
from briefcase.console import Log
from briefcase.integrations.base import ToolCache
from tests.utils import DummyConsole


@pytest.fixture
def mock_tools(tmp_path) -> ToolCache:
    mock_tools = ToolCache(
        logger=Log(),
        console=DummyConsole(),
        base_path=tmp_path / "tools",
        home_path=tmp_path / "home",
    )

    # Mock stdlib tools
    mock_tools.os = MagicMock(spec_set=os)
    mock_tools.platform = MagicMock(spec_set=platform)
    mock_tools.shutil = MagicMock(spec_set=shutil)
    mock_tools.sys = MagicMock(spec_set=sys)

    # Mock an empty environment
    mock_tools.os.environ = {}

    # Create base directories
    mock_tools.base_path.mkdir(parents=True)
    mock_tools.home_path.mkdir(parents=True)

    return mock_tools


@pytest.fixture
def first_app_config():
    return AppConfig(
        app_name="first-app",
        project_name="First Project",
        formal_name="First App",
        author="Megacorp",
        bundle="com.example",
        version="0.0.1",
        description="The first simple app",
        sources=["src/first_app"],
    )
