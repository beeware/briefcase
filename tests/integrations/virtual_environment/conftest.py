import shutil
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from briefcase.console import Console
from briefcase.integrations.base import ToolCache
from briefcase.integrations.subprocess import NativeAppContext, Subprocess
from briefcase.integrations.virtual_environment import (
    NoOpVirtualEnvironment,
    VirtualEnvironment,
)


@pytest.fixture
def dummy_console():
    return MagicMock(spec_set=Console)


@pytest.fixture
def noop_venv(first_app, mock_tools, base_venv_path, tmp_path):
    return NoOpVirtualEnvironment(
        "desert",
        app=first_app,
        tools=mock_tools,
        base_path=base_venv_path,
        support_path=tmp_path / "support",
    )


class MockVirtualEnvironment(VirtualEnvironment):
    env_type: str = "mock_venv"

    @classmethod
    def verify(self):
        pass

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
        # The mock venv puts "rewrite" as the first argument of every call
        return ["rewrite", *args]

    def build_env(self, overrides):
        # The mock venv puts "VENV=active" in the environment dictionary
        env = overrides.copy() if overrides else {}
        env["VENV"] = "active"
        return env


@pytest.fixture
def mock_venv(first_app, mock_tools, base_venv_path, tmp_path):
    return MockVirtualEnvironment(
        "forest",
        app=first_app,
        tools=mock_tools,
        base_path=base_venv_path,
        support_path=tmp_path / "support",
    )


@pytest.fixture
def mock_POpen_instance():
    return MagicMock()


@pytest.fixture
def mock_tools(mock_tools, first_app, mock_POpen_instance) -> ToolCache:
    # Mock subprocess
    mock_tools.subprocess = MagicMock(spec_set=Subprocess)
    mock_tools.subprocess.run.return_value = 42
    mock_tools.subprocess.check_output.return_value = "command output"
    mock_tools.subprocess.Popen.return_value = mock_POpen_instance

    # Mock an app context for the first app
    NativeAppContext.verify(tools=mock_tools, app=first_app)
    return mock_tools
