import re
import subprocess
import sys
from unittest.mock import MagicMock

import pytest

from briefcase.exceptions import BriefcaseCommandError
from briefcase.integrations.virtual_environment import VenvEnvManager


def test_creates_when_missing(mock_tools, venv_path):
    """Prepare creates a venv via `python -m venv` and upgrades pip."""
    manager = VenvEnvManager(mock_tools, venv_path)
    manager._update_core_tools = MagicMock()
    mock_tools.subprocess.run = MagicMock()

    result = manager.prepare()

    assert result is True
    mock_tools.subprocess.run.assert_called_once_with(
        [sys.executable, "-m", "venv", venv_path],
        check=True,
    )
    manager._update_core_tools.assert_called_once()


def test_creates_parent_directory(mock_tools, tmp_path):
    """Prepare creates parent directories on demand."""
    venv = tmp_path / "nested" / "missing" / "test_venv"
    manager = VenvEnvManager(mock_tools, venv)
    manager._update_core_tools = MagicMock()
    mock_tools.subprocess.run = MagicMock()

    result = manager.prepare()

    assert result is True
    assert venv.parent.is_dir()


def test_idempotent_when_venv_exists(mock_tools, venv_path):
    """Prepare returns False and performs no work when the venv already exists."""
    venv_path.mkdir()
    (venv_path / "pyvenv.cfg").touch()

    manager = VenvEnvManager(mock_tools, venv_path)
    manager._update_core_tools = MagicMock()
    mock_tools.subprocess.run = MagicMock()

    result = manager.prepare()

    assert result is False
    mock_tools.subprocess.run.assert_not_called()
    manager._update_core_tools.assert_not_called()


def test_recreate(mock_tools, venv_path):
    """Prepare returns False and performs no work when the venv already exists."""
    venv_path.mkdir()
    (venv_path / "pyvenv.cfg").touch()

    manager = VenvEnvManager(mock_tools, venv_path)
    manager._update_core_tools = MagicMock()
    mock_tools.subprocess.run = MagicMock()

    result = manager.prepare(recreate=True)

    assert result is True
    mock_tools.subprocess.run.assert_called_once_with(
        [sys.executable, "-m", "venv", venv_path],
        check=True,
    )
    manager._update_core_tools.assert_called_once()


def test_prepare_subprocess_failure_raises(mock_tools, venv_path):
    """Prepare wraps CalledProcessError as BriefcaseCommandError."""
    manager = VenvEnvManager(mock_tools, venv_path)
    manager._update_core_tools = MagicMock()

    mock_tools.subprocess.run = MagicMock(
        side_effect=subprocess.CalledProcessError(returncode=1, cmd="venv")
    )

    escaped = re.escape(str(venv_path))
    with pytest.raises(
        BriefcaseCommandError,
        match=f"Failed to create virtual environment at {escaped}",
    ):
        manager.prepare()

    mock_tools.subprocess.run.assert_called_once_with(
        [sys.executable, "-m", "venv", venv_path],
        check=True,
    )
    manager._update_core_tools.assert_not_called()


def test_prepare_pip_upgrade_failure_raises(mock_tools, venv_path):
    """Prepare wraps pip-upgrade failures as BriefcaseCommandError."""
    manager = VenvEnvManager(mock_tools, venv_path)
    mock_tools.subprocess.run = MagicMock()

    # First subprocess.run call (venv creation) succeeds; the pip-upgrade step
    # is exercised by _update_core_tools, which we cause to raise.
    def raise_pip_upgrade(*args, **kwargs):  # pragma: no cover - inner helper
        raise RuntimeError("pip install failed")

    manager._update_core_tools = MagicMock(side_effect=RuntimeError("pip failed"))

    escaped = re.escape(str(venv_path))
    with pytest.raises(
        BriefcaseCommandError,
        match=f"Failed to update core tooling for {escaped}",
    ):
        manager.prepare()


def test_update_core_tools_runs_pip_install(mock_tools, venv_path):
    """_update_core_tools invokes the venv's Python to upgrade pip."""
    manager = VenvEnvManager(mock_tools, venv_path)
    mock_tools.subprocess.run = MagicMock()

    manager._update_core_tools()

    mock_tools.subprocess.run.assert_called_once_with(
        [manager.executable, "-m", "pip", "install", "-U", "pip"],
        check=True,
    )
