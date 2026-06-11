import os
import sys

import pytest

from briefcase.integrations.virtual_environment import VenvEnvManager


@pytest.fixture
def manager(mock_tools, venv_path):
    return VenvEnvManager(mock_tools, venv_path)


@pytest.fixture
def system_path():
    return (
        "C:\\Windows\\system32;C:\\Windows"
        if sys.platform == "win32"
        else "/system/bin"
    )


@pytest.fixture
def user_path():
    return "C:\\custom\\path" if sys.platform == "win32" else "/custom/path"


@pytest.fixture
def complex_path():
    return (
        "C:\\system\\bin;C:\\usr\\bin"
        if sys.platform == "win32"
        else "/system/bin:/usr/bin"
    )


@pytest.fixture
def venv_bin_dir():
    return "Scripts" if sys.platform == "win32" else "bin"


@pytest.mark.parametrize("overrides", [None, {}])
def test_empty(manager, complex_path, venv_bin_dir, overrides, monkeypatch):
    """Empty environments are augmented with venv extras."""
    monkeypatch.setenv("PATH", complex_path)

    result = manager.build_env(overrides)

    expected_path = str(manager.venv_path / venv_bin_dir) + os.pathsep + complex_path
    assert result["PATH"] == expected_path
    assert result["VIRTUAL_ENV"] == str(manager.venv_path)
    assert "PYTHONHOME" not in result


def test_base(manager, complex_path, venv_bin_dir, monkeypatch):
    """Environment overrides are augmented with venv values."""
    monkeypatch.setenv("PATH", complex_path)
    monkeypatch.setenv("PYTHONHOME", complex_path)

    result = manager.build_env({"VALUE": "value"})

    expected_path = str(manager.venv_path / venv_bin_dir) + os.pathsep + complex_path
    assert result["PATH"] == expected_path
    assert result["VIRTUAL_ENV"] == str(manager.venv_path)
    assert result["VALUE"] == "value"
    assert "PYTHONHOME" not in result


def test_overrides(manager, user_path, system_path, venv_bin_dir, monkeypatch):
    """User supplied values are overridden (or augmented in the case of PATH."""
    monkeypatch.setenv("PATH", system_path)
    monkeypatch.setenv("VIRTUAL_ENV", "base-venv-value")
    monkeypatch.setenv("PYTHONHOME", "base-pythonhome-value")
    monkeypatch.setenv("BASE", "base-env-value")

    result = manager.build_env(
        {
            "PATH": user_path,
            "VIRTUAL_ENV": "override-venv-value",
            "PYTHONHOME": "override-pythonhome-value",
            "OVERRIDE": "override-value",
        }
    )

    expected = str(manager.venv_path / venv_bin_dir) + os.pathsep + user_path
    assert result["PATH"] == expected
    assert result["VIRTUAL_ENV"] == str(manager.venv_path)
    assert result["OVERRIDE"] == "override-value"
    assert "PYTHONHOME" not in result


def test_path_override_none_falls_back_to_system(
    manager,
    system_path,
    venv_bin_dir,
    monkeypatch,
):
    """A None PATH override falls back to the ambient PATH."""
    monkeypatch.setenv("PATH", system_path)

    result = manager.build_env({"PATH": None})

    expected = str(manager.venv_path / venv_bin_dir) + os.pathsep + system_path
    assert result["PATH"] == expected


def test_path_override_empty_falls_back_to_system(
    manager,
    system_path,
    venv_bin_dir,
    monkeypatch,
):
    """An empty PATH override falls back to the ambient PATH."""
    monkeypatch.setenv("PATH", system_path)

    result = manager.build_env({"PATH": ""})

    expected = str(manager.venv_path / venv_bin_dir) + os.pathsep + system_path
    assert result["PATH"] == expected


def test_no_system_path(manager, venv_bin_dir, monkeypatch):
    """When no PATH is set anywhere, only the venv's bin_dir contributes."""
    monkeypatch.delenv("PATH", raising=False)

    result = manager.build_env(None)

    assert result["PATH"] == str(manager.venv_path / venv_bin_dir)
