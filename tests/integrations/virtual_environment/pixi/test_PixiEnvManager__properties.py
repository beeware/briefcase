import os
import sys
from pathlib import Path

import pytest


@pytest.fixture
def env_path(venv_path):
    return venv_path / ".pixi" / "envs" / "default"


@pytest.mark.skipif(sys.platform == "win32", reason="Unix specific test")
def test_bin_dir_unix(venv, env_path):
    """bin_dir returns the default environment's 'bin' directory on Unix."""
    result = venv.bin_dir
    assert result == env_path / "bin"
    assert isinstance(result, Path)


@pytest.mark.skipif(sys.platform != "win32", reason="Windows specific test")
def test_bin_dir_windows(venv, env_path):
    """bin_dir returns the default environment's directory on Windows."""
    result = venv.bin_dir
    assert result == env_path
    assert isinstance(result, Path)


def test_env_path(venv, env_path):
    """env_path points at the materialised default environment."""
    assert venv.env_path == env_path


@pytest.mark.skipif(sys.platform == "win32", reason="Unix specific test")
def test_executable_unix(venv):
    """Executable returns 'python' under bin/ on Unix systems."""
    result = venv.executable
    assert isinstance(result, Path)
    assert os.path.isabs(result)
    assert result.name == "python"
    assert result == venv.bin_dir / "python"


@pytest.mark.skipif(sys.platform != "win32", reason="Windows specific test")
def test_executable_windows(venv):
    """Executable returns 'python.exe' on Windows systems."""
    result = venv.executable
    assert isinstance(result, Path)
    assert os.path.isabs(result)
    assert result.name == "python.exe"
    assert result == venv.bin_dir / "python.exe"


def test_python_version(venv):
    """The python_version property reflects the active interpreter."""
    assert venv.python_version == f"{sys.version_info.major}.{sys.version_info.minor}"
