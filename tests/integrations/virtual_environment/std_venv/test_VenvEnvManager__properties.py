import os
import sys
from pathlib import Path

import pytest

from briefcase.integrations.virtual_environment import VenvEnvManager


@pytest.fixture
def manager(mock_tools, venv_path):
    return VenvEnvManager(mock_tools, venv_path)


@pytest.mark.skipif(sys.platform == "win32", reason="Unix specific test")
def test_bin_dir_unix(manager, venv_path):
    """bin_dir returns 'bin' directory on Unix systems."""
    result = manager.bin_dir
    assert result == venv_path / "bin"
    assert isinstance(result, Path)


@pytest.mark.skipif(sys.platform != "win32", reason="Windows specific test")
def test_bin_dir_windows(manager, venv_path):
    """bin_dir returns 'Scripts' directory on Windows."""
    result = manager.bin_dir
    assert result == venv_path / "Scripts"
    assert isinstance(result, Path)


@pytest.mark.skipif(sys.platform == "win32", reason="Unix specific test")
def test_executable_unix(manager):
    """Executable returns 'python' under bin/ on Unix systems."""
    result = manager.executable
    assert isinstance(result, Path)
    assert os.path.isabs(result)
    assert result.name == "python"
    assert result == manager.bin_dir / "python"


@pytest.mark.skipif(sys.platform != "win32", reason="Windows specific test")
def test_executable_windows(manager):
    """Executable returns 'python.exe' under Scripts\\ on Windows systems."""
    result = manager.executable
    assert isinstance(result, Path)
    assert os.path.isabs(result)
    assert result.name == "python.exe"
    assert result == manager.bin_dir / "python.exe"
