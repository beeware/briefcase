import os
import sys
from unittest.mock import patch

import pytest


@pytest.fixture
def platform_paths():
    """Platform-appropriate mock paths for testing."""
    if sys.platform == "win32":
        return {
            "system": "C:\\Windows\\system32;C:\\Windows",
            "user": "C:\\custom\\path",
            "complex": "C:\\system\\bin;C:\\usr\\bin",
            "empty": "",
        }
    return {
        "system": "/system/bin",
        "user": "/custom/path",
        "complex": "/system/bin:/usr/bin",
        "empty": "",
    }


@pytest.fixture
def venv_bin_dir():
    """Platform-appropriate virtual environment binary directory."""
    return "Scripts" if sys.platform == "win32" else "bin"


@pytest.fixture
def path_separator():
    """Platform-appropriate PATH separator."""
    return os.pathsep


@pytest.mark.parametrize("overrides", [None, {}, {"VALUE": "value"}])
def test_full_env_basic_creation(
    venv_context, platform_paths, venv_bin_dir, path_separator, overrides
):
    """Test that full_env creates an environment with expected defaults."""
    with patch.dict(os.environ, {"PATH": platform_paths["complex"]}, clear=False):
        result = venv_context.full_env(overrides)

        expected_path_ending = f"test_venv{os.sep}{venv_bin_dir}{path_separator}{platform_paths['complex']}"
        assert result["PATH"].endswith(expected_path_ending)
        assert result["VIRTUAL_ENV"].endswith("test_venv")

        if overrides and "VALUE" in overrides:
            assert result["VALUE"] == "value"


def test_full_env_path_override_custom_path_with_system(
    venv_context, platform_paths, venv_bin_dir, path_separator
):
    """Test full_env with custom PATH override and system PATH."""
    overrides = {"PATH": platform_paths["user"]}

    with patch.dict(os.environ, {"PATH": platform_paths["system"]}, clear=False):
        result = venv_context.full_env(overrides)

        expected_path_ending = (
            f"test_venv{os.sep}{venv_bin_dir}{path_separator}{platform_paths['user']}"
        )
        assert result["PATH"].endswith(expected_path_ending)
        assert result["VIRTUAL_ENV"].endswith("test_venv")


def test_full_env_path_override_none_with_system(
    venv_context, platform_paths, venv_bin_dir, path_separator
):
    """Test full_env with None PATH override and system PATH."""
    overrides = {"PATH": None}

    with patch.dict(os.environ, {"PATH": platform_paths["system"]}, clear=False):
        result = venv_context.full_env(overrides)

        expected_path_ending = (
            f"test_venv{os.sep}{venv_bin_dir}{path_separator}{platform_paths['system']}"
        )
        assert result["PATH"].endswith(expected_path_ending)
        assert result["VIRTUAL_ENV"].endswith("test_venv")


def test_full_env_path_override_empty_with_system(
    venv_context, platform_paths, venv_bin_dir, path_separator
):
    """Test full_env with empty PATH override and system PATH."""
    overrides = {"PATH": platform_paths["empty"]}

    with patch.dict(os.environ, {"PATH": platform_paths["system"]}, clear=False):
        result = venv_context.full_env(overrides)

        expected_path_ending = (
            f"test_venv{os.sep}{venv_bin_dir}{path_separator}{platform_paths['system']}"
        )
        assert result["PATH"].endswith(expected_path_ending)
        assert result["VIRTUAL_ENV"].endswith("test_venv")


def test_full_env_path_override_custom_with_empty_system(
    venv_context, platform_paths, venv_bin_dir, path_separator
):
    """Test full_env with custom PATH override and empty system PATH."""
    overrides = {"PATH": platform_paths["user"]}

    with patch.dict(os.environ, {"PATH": platform_paths["empty"]}, clear=False):
        result = venv_context.full_env(overrides)

        expected_path_ending = (
            f"test_venv{os.sep}{venv_bin_dir}{path_separator}{platform_paths['user']}"
        )
        assert result["PATH"].endswith(expected_path_ending)
        assert result["VIRTUAL_ENV"].endswith("test_venv")


def test_full_env_path_override_none_with_empty_system(
    venv_context, platform_paths, venv_bin_dir
):
    """Test full_env with None PATH override and empty system PATH."""
    overrides = {"PATH": None}

    with patch.dict(os.environ, {"PATH": platform_paths["empty"]}, clear=False):
        result = venv_context.full_env(overrides)

        expected_path_ending = f"test_venv{os.sep}{venv_bin_dir}"
        assert result["PATH"].endswith(expected_path_ending)
        assert result["VIRTUAL_ENV"].endswith("test_venv")


def test_full_env_no_overrides(
    venv_context, platform_paths, venv_bin_dir, path_separator
):
    """Test full_env with no overrides parameter."""
    with patch.dict(os.environ, {"PATH": platform_paths["system"]}, clear=False):
        result = venv_context.full_env(None)

        expected_path_ending = (
            f"test_venv{os.sep}{venv_bin_dir}{path_separator}{platform_paths['system']}"
        )
        assert result["PATH"].endswith(expected_path_ending)
        assert result["VIRTUAL_ENV"].endswith("test_venv")


def test_full_env_no_system_path(venv_context, venv_bin_dir):
    """Test full_env when system has no PATH."""
    with patch.dict(os.environ, {}, clear=True):
        result = venv_context.full_env(None)

        expected_path_ending = f"test_venv{os.sep}{venv_bin_dir}"
        assert result["PATH"].endswith(expected_path_ending)
        assert result["VIRTUAL_ENV"].endswith("test_venv")
