import os
from unittest.mock import patch

import pytest

from briefcase.integrations.virtual_environment import VenvContext


class TestFullEnv:
    """Test cases for the VenvContext.full_env property."""

    @pytest.mark.parametrize("overrides", [None, {}, {"VALUE": "value"}])
    def test_full_env_basic_creation(self, venv_context: VenvContext, overrides):
        """Test that full_env creates an environment with expected defaults."""
        with patch.dict(os.environ, {"PATH": "/system/bin:/usr/bin"}, clear=False):
            result = venv_context.full_env(overrides)
            expected_path = f"{venv_context.bin_dir}{os.pathsep}/system/bin:/usr/bin"
            assert result["PATH"] == expected_path
            assert result["VIRTUAL_ENV"] == str(venv_context.venv_path)
            if overrides and "VALUE" in overrides:  # probs need to change this
                assert result["VALUE"] == "value"

    @pytest.mark.parametrize(
        "path_override, system_path, expected_suffix",
        [
            ("/custom/path", "/system/bin", "/custom/path"),
            (None, "/system/bin", "/system/bin"),
            ("", "/system/bin", "/system/bin"),
            ("/custom/path", "", "/custom/path"),
            (None, "", ""),
        ],
    )
    def test_full_env_path_overrides(
        self, venv_context: VenvContext, path_override, system_path, expected_suffix
    ):
        """Test full_env handles PATH override logic correctly."""
        overrides = (
            {"PATH": path_override}
            if path_override is not None
            else {"PATH": path_override}
        )

        with patch.dict(os.environ, {"PATH": system_path}, clear=False):
            result = venv_context.full_env(overrides)

            if expected_suffix:
                expected_path = f"{venv_context.bin_dir}{os.pathsep}{expected_suffix}"
            else:
                expected_path = str(venv_context.bin_dir)

            assert result["PATH"] == expected_path
            assert result["VIRTUAL_ENV"] == str(venv_context.venv_path)

    @pytest.mark.skipif(os.name != "nt", reason="Windows-specific test")
    def test_full_env_windows_pythonhome_removal(self, venv_context: VenvContext):
        """Test full_env removes PYTHONHOME on Windows."""
        overrides = {"PYTHONHOME": "/old/python", "CUSTOM": "value"}

        with patch.dict(os.environ, {"PATH": "/system/bin"}, clear=False):
            result = venv_context.full_env(overrides)

            assert "PYTHONHOME" not in result
            assert result["CUSTOM"] == "value"
            assert "PATH" in result
            assert "VIRTUAL_ENV" in result

    # TODO: test this on lab machine
    @pytest.mark.skipif(os.name == "nt", reason="Unix-specific test")
    def test_full_env_unix_no_pythonhome_handling(self, venv_context: VenvContext):
        """Test full_env preserves PYTHONHOME on Unix systems."""
        overrides = {"PYTHONHOME": "/old/python", "CUSTOM": "value"}

        with patch.dict(os.environ, {"PATH": "/system/bin"}, clear=False):
            result = venv_context.full_env(overrides)

            assert result["PYTHONHOME"] == "/old/python"
            assert result["CUSTOM"] == "value"
            assert "PATH" in result
            assert "VIRTUAL_ENV" in result
