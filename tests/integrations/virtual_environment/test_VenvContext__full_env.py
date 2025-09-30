import os
import sys

import pytest


@pytest.fixture
def system_path():
    """System PATH for testing."""
    return (
        "C:\\Windows\\system32;C:\\Windows"
        if sys.platform == "win32"
        else "/system/bin"
    )


@pytest.fixture
def user_path():
    """User PATH for testing."""
    return "C:\\custom\\path" if sys.platform == "win32" else "/custom/path"


@pytest.fixture
def complex_path():
    """Complex PATH with multiple entries for testing."""
    return (
        "C:\\system\\bin;C:\\usr\\bin"
        if sys.platform == "win32"
        else "/system/bin:/usr/bin"
    )


@pytest.fixture
def empty_path():
    """Empty PATH for testing."""
    return ""


@pytest.fixture
def venv_bin_dir():
    """Platform-appropriate virtual environment binary directory."""
    return "Scripts" if sys.platform == "win32" else "bin"


@pytest.mark.parametrize("overrides", [None, {}, {"VALUE": "value"}])
def test_full_env_basic_creation(
    venv_context,
    complex_path,
    venv_bin_dir,
    overrides,
    monkeypatch,
):
    """full_env creates an environment with expected defaults."""
    monkeypatch.setenv("PATH", complex_path)

    result = venv_context.full_env(overrides)

    expected_path = (
        str(venv_context.venv_path / venv_bin_dir) + os.pathsep + complex_path
    )
    assert result["PATH"] == expected_path
    assert result["VIRTUAL_ENV"] == str(venv_context.venv_path)

    if overrides and "VALUE" in overrides:
        assert result["VALUE"] == "value"

    assert "PYTHONHOME" not in result


def test_full_env_path_override_custom_path_with_system(
    venv_context,
    user_path,
    system_path,
    venv_bin_dir,
    monkeypatch,
):
    """A path provided as an override supersedes the system path, but is augmented with
    the venv path."""
    overrides = {"PATH": user_path}
    monkeypatch.setenv("PATH", system_path)

    result = venv_context.full_env(overrides)

    expected_path = str(venv_context.venv_path / venv_bin_dir) + os.pathsep + user_path
    assert result["PATH"] == expected_path
    assert result["VIRTUAL_ENV"] == str(venv_context.venv_path)
    assert "PYTHONHOME" not in result


def test_full_env_path_override_none_with_system(
    venv_context,
    system_path,
    venv_bin_dir,
    monkeypatch,
):
    """A None PATH override falls back to system PATH, augmented with venv path."""
    overrides = {"PATH": None}
    monkeypatch.setenv("PATH", system_path)

    result = venv_context.full_env(overrides)

    expected_path = (
        str(venv_context.venv_path / venv_bin_dir) + os.pathsep + system_path
    )
    assert result["PATH"] == expected_path
    assert result["VIRTUAL_ENV"] == str(venv_context.venv_path)
    assert "PYTHONHOME" not in result


def test_full_env_path_override_empty_with_system(
    venv_context,
    empty_path,
    system_path,
    venv_bin_dir,
    monkeypatch,
):
    """An empty PATH override falls back to system PATH, augmented with venv path."""
    overrides = {"PATH": empty_path}
    monkeypatch.setenv("PATH", system_path)

    result = venv_context.full_env(overrides)

    expected_path = (
        str(venv_context.venv_path / venv_bin_dir) + os.pathsep + system_path
    )
    assert result["PATH"] == expected_path
    assert result["VIRTUAL_ENV"] == str(venv_context.venv_path)
    assert "PYTHONHOME" not in result


def test_full_env_path_override_custom_with_empty_system(
    venv_context,
    user_path,
    empty_path,
    venv_bin_dir,
    monkeypatch,
):
    """Custom PATH override is used even when system PATH is empty."""
    overrides = {"PATH": user_path}
    monkeypatch.setenv("PATH", empty_path)

    result = venv_context.full_env(overrides)

    expected_path = str(venv_context.venv_path / venv_bin_dir) + os.pathsep + user_path
    assert result["PATH"] == expected_path
    assert result["VIRTUAL_ENV"] == str(venv_context.venv_path)
    assert "PYTHONHOME" not in result


def test_full_env_path_override_none_with_empty_system(
    venv_context,
    empty_path,
    venv_bin_dir,
    monkeypatch,
):
    """When both override and system PATH are empty, only venv path is used."""
    overrides = {"PATH": None}
    monkeypatch.setenv("PATH", empty_path)

    result = venv_context.full_env(overrides)

    expected_path = str(venv_context.venv_path / venv_bin_dir)
    assert result["PATH"] == expected_path
    assert result["VIRTUAL_ENV"] == str(venv_context.venv_path)
    assert "PYTHONHOME" not in result


def test_full_env_no_overrides(
    venv_context,
    system_path,
    venv_bin_dir,
    monkeypatch,
):
    """full_env with no overrides parameter uses system PATH."""
    monkeypatch.setenv("PATH", system_path)

    result = venv_context.full_env(None)

    expected_path = (
        str(venv_context.venv_path / venv_bin_dir) + os.pathsep + system_path
    )
    assert result["PATH"] == expected_path
    assert result["VIRTUAL_ENV"] == str(venv_context.venv_path)
    assert "PYTHONHOME" not in result


def test_full_env_no_system_path(
    venv_context,
    venv_bin_dir,
    monkeypatch,
):
    """When no system PATH exists, only venv path is used."""
    monkeypatch.delenv("PATH", raising=False)

    result = venv_context.full_env(None)

    expected_path = str(venv_context.venv_path / venv_bin_dir)
    assert result["PATH"] == expected_path
    assert result["VIRTUAL_ENV"] == str(venv_context.venv_path)
    assert "PYTHONHOME" not in result
