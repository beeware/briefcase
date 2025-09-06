from pathlib import Path
from unittest.mock import patch

import pytest

from briefcase.integrations.virtual_environment import VenvContext


class TestVirtualEnvironmentContextBinDir:
    """Tests for VenvContext.bin_dir property."""

    def test_bin_dir_unix(self, dummy_tools, tmp_path):
        """Test bin_dir returns 'bin' directory on Unix systems."""
        venv_path = tmp_path / "test_venv"
        context = VenvContext(dummy_tools, venv_path)

        with patch("os.name", "posix"):
            result = context.bin_dir

        expected = venv_path / "bin"
        assert result == expected
        assert isinstance(result, Path)

    def test_bin_dir_windows(self, dummy_tools, tmp_path):
        """Test bin_dir returns 'Scripts' directory on Windows."""
        venv_path = tmp_path / "test_venv"
        context = VenvContext(dummy_tools, venv_path)

        with patch("os.name", "nt"):
            result = context.bin_dir

        expected = venv_path / "Scripts"
        assert result == expected
        assert isinstance(result, Path)

    @pytest.mark.parametrize(
        "venv_path",
        [
            Path("/home/user/venvs/myproject"),
            Path("relative/path/venv"),
            Path("/tmp/venv"),
            Path("C:\\Users\\User\\venv"),
        ],
    )
    def test_bin_dir_different_venv_paths(self, dummy_tools, venv_path):
        """Test bin_dir works with different venv path structures."""
        context = VenvContext(dummy_tools, venv_path)

        with patch("os.name", "posix"):
            unix_result = context.bin_dir
            assert unix_result == venv_path / "bin"

        with patch("os.name", "nt"):
            windows_result = context.bin_dir
            assert windows_result == venv_path / "Scripts"
