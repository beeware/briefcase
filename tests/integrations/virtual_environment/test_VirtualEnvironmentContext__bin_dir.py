import sys
from pathlib import Path

import pytest

from briefcase.integrations.virtual_environment import VenvContext


@pytest.mark.skipif(sys.platform == "win32", reason="Unix specific bin directory test")
def test_bin_dir_unix(dummy_tools, tmp_path):
    """Test bin_dir returns 'bin' directory on Unix systems."""
    venv_path = tmp_path / "test_venv"
    context = VenvContext(dummy_tools, venv_path)

    result = context.bin_dir

    expected = venv_path / "bin"
    assert result == expected
    assert isinstance(result, Path)


@pytest.mark.skipif(
    sys.platform != "win32", reason="Windows specific bin directory test"
)
def test_bin_dir_windows(dummy_tools, tmp_path):
    """Test bin_dir returns 'Scripts' directory on Windows."""
    venv_path = tmp_path / "test_venv"
    context = VenvContext(dummy_tools, venv_path)

    result = context.bin_dir
    expected = venv_path / "Scripts"
    assert result == expected
    assert isinstance(result, Path)


@pytest.mark.parametrize(
    "venv_path",
    [
        Path("C:\\Users\\User\\venv"),
        Path("relative\\path\\venv"),
        Path("D:\\Projects\\myapp\\venv"),
    ],
)
@pytest.mark.skipif(sys.platform != "win32", reason="Windows specific test")
def test_bin_dir_different_venv_paths(dummy_tools, venv_path):
    """Test bin_dir works with different venv path structures."""
    context = VenvContext(dummy_tools, venv_path)
    windows_result = context.bin_dir
    assert windows_result == venv_path / "Scripts"


@pytest.mark.parametrize(
    "venv_path",
    [
        Path("/home/user/venvs/myproject"),
        Path("relative/path/venv"),
        Path("/tmp/venv"),
    ],
)
@pytest.mark.skipif(sys.platform == "win32", reason="Unix specific test")
def test_bin_dir_different_venv_paths_unix(dummy_tools, venv_path):
    """Test bin_dir works with different venv path structures."""
    context = VenvContext(dummy_tools, venv_path)
    unix_result = context.bin_dir
    assert unix_result == venv_path / "bin"
