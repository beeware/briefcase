import os
from unittest.mock import patch

import pytest

from briefcase.integrations.virtual_environment import VenvContext


@pytest.mark.parametrize("overrides", [None, {}, {"VALUE": "value"}])
def test_full_env_basic_creation(self, venv_context: VenvContext, overrides):
    """Test that full_env creates an environment with expected defaults."""
    with patch.dict(os.environ, {"PATH": "/system/bin:/usr/bin"}, clear=False):
        result = venv_context.full_env(overrides)

        assert result["PATH"].endswith("test_venv/bin:/system/bin:/usr/bin")
        assert result["VIRTUAL_ENV"].endswith("test_venv")

        if overrides and "VALUE" in overrides:
            assert result["VALUE"] == "value"


def test_full_env_path_override_custom_path_with_system(
    self, venv_context: VenvContext
):
    """Test full_env with custom PATH override and system PATH."""
    overrides = {"PATH": "/custom/path"}

    with patch.dict(os.environ, {"PATH": "/system/bin"}, clear=False):
        result = venv_context.full_env(overrides)

        assert result["PATH"].endswith("test_venv/bin:/custom/path")
        assert result["VIRTUAL_ENV"].endswith("test_venv")


def test_full_env_path_override_none_with_system(self, venv_context: VenvContext):
    """Test full_env with None PATH override and system PATH."""
    overrides = {"PATH": None}

    with patch.dict(os.environ, {"PATH": "/system/bin"}, clear=False):
        result = venv_context.full_env(overrides)

        assert result["PATH"].endswith("test_venv/bin:/system/bin")
        assert result["VIRTUAL_ENV"].endswith("test_venv")


def test_full_env_path_override_empty_with_system(self, venv_context: VenvContext):
    """Test full_env with empty PATH override and system PATH."""
    overrides = {"PATH": ""}

    with patch.dict(os.environ, {"PATH": "/system/bin"}, clear=False):
        result = venv_context.full_env(overrides)

        assert result["PATH"].endswith("test_venv/bin:/system/bin")
        assert result["VIRTUAL_ENV"].endswith("test_venv")


def test_full_env_path_override_custom_with_empty_system(
    self, venv_context: VenvContext
):
    """Test full_env with custom PATH override and empty system PATH."""
    overrides = {"PATH": "/custom/path"}

    with patch.dict(os.environ, {"PATH": ""}, clear=False):
        result = venv_context.full_env(overrides)

        assert result["PATH"].endswith("test_venv/bin:/custom/path")
        assert result["VIRTUAL_ENV"].endswith("test_venv")


def test_full_env_path_override_none_with_empty_system(self, venv_context: VenvContext):
    """Test full_env with None PATH override and empty system PATH."""
    overrides = {"PATH": None}

    with patch.dict(os.environ, {"PATH": ""}, clear=False):
        result = venv_context.full_env(overrides)

        assert result["PATH"].endswith("test_venv/bin")
        assert result["VIRTUAL_ENV"].endswith("test_venv")


@pytest.mark.skipif(os.name != "nt", reason="Windows-specific test")
def test_full_env_windows_pythonhome_removal(self, venv_context: VenvContext):
    """Test full_env removes PYTHONHOME on Windows."""
    overrides = {"PYTHONHOME": "/old/python", "CUSTOM": "value"}

    with patch.dict(os.environ, {"PATH": "/system/bin"}, clear=False):
        result = venv_context.full_env(overrides)

        assert "PYTHONHOME" not in result
        assert result["CUSTOM"] == "value"
        assert result["PATH"].endswith("test_venv/Scripts:/system/bin")
        assert result["VIRTUAL_ENV"].endswith("test_venv")


@pytest.mark.skipif(os.name == "nt", reason="Unix-specific test")
def test_full_env_unix_no_pythonhome_handling(self, venv_context: VenvContext):
    """Test full_env preserves PYTHONHOME on Unix systems."""
    overrides = {"PYTHONHOME": "/old/python", "CUSTOM": "value"}

    with patch.dict(os.environ, {"PATH": "/system/bin"}, clear=False):
        result = venv_context.full_env(overrides)

        assert result["PYTHONHOME"] == "/old/python"
        assert result["CUSTOM"] == "value"
        assert result["PATH"].endswith("test_venv/bin:/system/bin")
        assert result["VIRTUAL_ENV"].endswith("test_venv")


def test_full_env_no_overrides(self, venv_context: VenvContext):
    """Test full_env with no overrides parameter."""
    with patch.dict(os.environ, {"PATH": "/system/bin"}, clear=False):
        result = venv_context.full_env(None)

        assert result["PATH"].endswith("test_venv/bin:/system/bin")
        assert result["VIRTUAL_ENV"].endswith("test_venv")


def test_full_env_no_system_path(self, venv_context: VenvContext):
    """Test full_env when system has no PATH."""
    with patch.dict(os.environ, {}, clear=True):
        result = venv_context.full_env(None)

        assert result["PATH"].endswith("test_venv/bin")
        assert result["VIRTUAL_ENV"].endswith("test_venv")
