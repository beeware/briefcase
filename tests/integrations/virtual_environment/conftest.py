from unittest.mock import MagicMock

import pytest

from briefcase.console import Console
from briefcase.integrations.base import ToolCache
from briefcase.integrations.subprocess import Subprocess
from briefcase.integrations.virtual_environment import (
    NoOpEnvManager,
)


@pytest.fixture
def dummy_console():
    return MagicMock(spec_set=Console)


@pytest.fixture
def venv_path(tmp_path):
    return tmp_path / "test_venv"


@pytest.fixture
def noop_manager(mock_tools, venv_path):
    return NoOpEnvManager(mock_tools, venv_path)


@pytest.fixture
def simple_manager():
    # Define a test manager that adds "rewrite" to the start of
    # every argument list, and adds "VENV" to the environment
    manager = MagicMock()

    def rewrite_args(args):
        return ["rewrite", *args]

    def build_env(overrides):
        env = overrides.copy() if overrides else {}
        env["VENV"] = "active"
        return env

    manager.rewrite_args = rewrite_args
    manager.build_env = build_env

    return manager


@pytest.fixture
def process():
    return MagicMock()


@pytest.fixture
def mock_tools(mock_tools, process) -> ToolCache:
    # Mock subprocess
    mock_tools.subprocess = MagicMock(spec_set=Subprocess)
    mock_tools.subprocess.run.return_value = 42
    mock_tools.subprocess.check_output.return_value = "command output"
    mock_tools.subprocess.Popen.return_value = process
    return mock_tools
