from unittest.mock import MagicMock

import pytest

from briefcase.console import Console
from briefcase.integrations.virtual_environment import VenvContext


@pytest.fixture
def dummy_console():
    return MagicMock(spec_set=Console)


@pytest.fixture
def venv_path(tmp_path):
    return tmp_path / "test_venv"


@pytest.fixture
def venv_context(mock_tools, venv_path):
    return VenvContext(
        tools=mock_tools,
        venv_path=venv_path,
    )


@pytest.fixture
def mock_subprocess_setup(venv_context, monkeypatch):
    """Setup mock objects for subprocess testing across all VenvContext tests."""
    mock_rewrite_head = MagicMock(return_value=["rewritten", "args"])
    mock_full_env = MagicMock(return_value={"FULL": "env"})
    mock_subprocess = MagicMock()

    mock_popen_instance = MagicMock()
    mock_completed_process = MagicMock()

    mock_subprocess.Popen.return_value = mock_popen_instance
    mock_subprocess.run.return_value = mock_completed_process
    mock_subprocess.check_output.return_value = "output"

    monkeypatch.setattr(venv_context, "_rewrite_head", mock_rewrite_head)
    monkeypatch.setattr(venv_context, "full_env", mock_full_env)
    monkeypatch.setattr(venv_context.tools, "subprocess", mock_subprocess)

    return {
        "rewrite_head": mock_rewrite_head,
        "full_env": mock_full_env,
        "subprocess": mock_subprocess,
        "popen_instance": mock_popen_instance,
        "completed_process": mock_completed_process,
    }
