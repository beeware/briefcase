import os
import sys
from pathlib import Path

import pytest


@pytest.mark.skipif(sys.platform == "win32", reason="Unix specific test")
def test_executable_unix(venv_context):
    """Executable property returns correct path on Unix systems."""
    result = venv_context.executable

    # Should be absolute path
    assert os.path.isabs(result)
    assert isinstance(result, Path)

    # Should end with python (no .exe on Unix)
    assert result.name == "python"

    # Should be the exact expected path
    expected_path = venv_context.bin_dir / "python"
    assert result == expected_path


@pytest.mark.skipif(sys.platform != "win32", reason="Windows specific test")
def test_executable_windows(venv_context):
    """Executable property returns correct path on Windows systems."""
    result = venv_context.executable

    # Should be absolute path
    assert os.path.isabs(result)
    assert isinstance(result, Path)

    # Should end with python.exe on Windows
    assert result.name == "python.exe"

    # Should be the exact expected path
    expected_path = venv_context.bin_dir / "python.exe"
    assert result == expected_path
