import shutil
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from briefcase.console import Console
from briefcase.integrations.base import ToolCache
from briefcase.integrations.subprocess import Subprocess
from briefcase.integrations.virtual_environment import (
    NoOpVirtualEnvironment,
    VirtualEnvironment,
)


@pytest.fixture
def dummy_console():
    return MagicMock(spec_set=Console)


@pytest.fixture
def venv_path(tmp_path):
    return tmp_path / "test_venv"


@pytest.fixture
def noop_venv(mock_tools, venv_path):
    return NoOpVirtualEnvironment(mock_tools, venv_path)


class MockVirtualEnvironment(VirtualEnvironment):
    @property
    def executable(self) -> Path:
        return self.venv_path / "something/bin/python"

    @property
    def bin_dir(self) -> Path:
        return self.executable.parent

    def exists(self) -> bool:
        return (self.venv_path / "something").exists()

    def prepare(self, recreate=False) -> bool:
        if not self.exists() or recreate:
            marker = self.venv_path / "something/marker"
            marker.parent.mkdir(parents=True, exist_ok=True)
            marker.write_text("mock env", encoding="utf-8")
            created = True
        else:
            created = False

        return created

    def clean(self) -> None:
        """Unlink the marker file if present."""
        if (self.venv_path / "something").exists():
            shutil.rmtree(self.venv_path / "something")

    def rewrite_args(self, args):
        return ["rewrite", *args]

    def build_env(self, overrides):
        env = overrides.copy() if overrides else {}
        env["VENV"] = "active"
        return env


@pytest.fixture
def mock_venv(mock_tools, venv_path):
    return MockVirtualEnvironment(mock_tools, venv_path)


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
