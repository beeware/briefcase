import os
import sys
from pathlib import Path

import pytest


@pytest.mark.skipif(sys.platform == "win32", reason="Unix specific test")
def test_bin_dir_unix(venv, venv_path):
    """bin_dir returns 'bin' directory on Unix systems."""
    result = venv.bin_dir
    assert result == venv_path / "bin"
    assert isinstance(result, Path)


@pytest.mark.skipif(sys.platform != "win32", reason="Windows specific test")
def test_bin_dir_windows(venv, venv_path):
    """bin_dir returns 'Scripts' directory on Windows."""
    result = venv.bin_dir
    assert result == venv_path / "Scripts"
    assert isinstance(result, Path)


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
    """Executable returns 'python.exe' under Scripts\\ on Windows systems."""
    result = venv.executable
    assert isinstance(result, Path)
    assert os.path.isabs(result)
    assert result.name == "python.exe"
    assert result == venv.bin_dir / "python.exe"


def test_python_version(venv):
    """The python_version property reflects the active interpreter."""
    assert venv.python_version == f"{sys.version_info.major}.{sys.version_info.minor}"
