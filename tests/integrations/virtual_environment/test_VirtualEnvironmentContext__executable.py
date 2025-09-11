import os
import sys

import pytest

from briefcase.integrations.virtual_environment import VenvContext



"""Test cases for VenvContext.executable property."""

@pytest.mark.skipif(sys.platform == "win32", reason="Unix specific test")
def test_executable_platform_specific_naming(self, venv_context):
    """Test executable property uses correct filename for each platform."""

    result = venv_context.executable

    assert result.endswith("python")
    assert isinstance(result, str)
    assert str(venv_context.bin_dir) in result

@pytest.mark.skipif(sys.platform != "win32", reason="Windows specific test")
def test_executable_windows_naming(self, venv_context):
    """Test executable property uses correct filename for each platform."""
    result = venv_context.executable

    assert result.endswith("python")
    assert isinstance(result, str)
    assert str(venv_context.bin_dir) in result

def test_executable_path_construction(self, venv_context: VenvContext):
    """Test executable property constructs correct path."""
    result = venv_context.executable

    assert isinstance(result, str)
    assert os.path.isabs(result)

    assert str(venv_context.venv_path) in result

    assert str(venv_context.bin_dir) in result

def test_executable_uses_bin_dir(self, venv_context: VenvContext):
    """Test executable property correctly uses bin_dir."""

    expected_filename = "python.exe" if os.name == "nt" else "python"
    expected_path = str(venv_context.bin_dir / expected_filename)

    result = venv_context.executable

    assert result == expected_path
