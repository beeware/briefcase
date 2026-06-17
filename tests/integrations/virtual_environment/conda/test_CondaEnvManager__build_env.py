import os
import sys

import pytest


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
def test_empty(venv, complex_path, venv_bin_dir, overrides, monkeypatch):
    """Empty environments are augmented with conda extras."""
    monkeypatch.setenv("PATH", complex_path)

    result = venv.build_env(overrides)

    expected_path = str(venv.venv_path / venv_bin_dir) + os.pathsep + complex_path
    assert result["PATH"] == expected_path
    assert result["CONDA_PREFIX"] == str(venv.venv_path)
    assert "PYTHONHOME" not in result


def test_base(venv, complex_path, venv_bin_dir, monkeypatch):
    """Environment overrides are augmented with conda values."""
    monkeypatch.setenv("PATH", complex_path)
    monkeypatch.setenv("PYTHONHOME", complex_path)

    result = venv.build_env({"VALUE": "value"})

    expected_path = str(venv.venv_path / venv_bin_dir) + os.pathsep + complex_path
    assert result["PATH"] == expected_path
    assert result["CONDA_PREFIX"] == str(venv.venv_path)
    assert result["VALUE"] == "value"
    assert "PYTHONHOME" not in result


def test_overrides(venv, user_path, system_path, venv_bin_dir, monkeypatch):
    """User supplied values are overridden (or augmented in the case of PATH)."""
    monkeypatch.setenv("PATH", system_path)
    monkeypatch.setenv("CONDA_PREFIX", "base-conda-value")
    monkeypatch.setenv("PYTHONHOME", "base-pythonhome-value")
    monkeypatch.setenv("BASE", "base-env-value")

    result = venv.build_env(
        {
            "PATH": user_path,
            "CONDA_PREFIX": "override-conda-value",
            "PYTHONHOME": "override-pythonhome-value",
            "OVERRIDE": "override-value",
        }
    )

    expected = str(venv.venv_path / venv_bin_dir) + os.pathsep + user_path
    assert result["PATH"] == expected
    assert result["CONDA_PREFIX"] == str(venv.venv_path)
    assert result["OVERRIDE"] == "override-value"
    assert "PYTHONHOME" not in result


def test_path_override_none_falls_back_to_system(
    venv,
    system_path,
    venv_bin_dir,
    monkeypatch,
):
    """A None PATH override falls back to the ambient PATH."""
    monkeypatch.setenv("PATH", system_path)

    result = venv.build_env({"PATH": None})

    expected = str(venv.venv_path / venv_bin_dir) + os.pathsep + system_path
    assert result["PATH"] == expected


def test_path_override_empty_falls_back_to_system(
    venv,
    system_path,
    venv_bin_dir,
    monkeypatch,
):
    """An empty PATH override falls back to the ambient PATH."""
    monkeypatch.setenv("PATH", system_path)

    result = venv.build_env({"PATH": ""})

    expected = str(venv.venv_path / venv_bin_dir) + os.pathsep + system_path
    assert result["PATH"] == expected


def test_no_system_path(venv, venv_bin_dir, monkeypatch):
    """When no PATH is set anywhere, only the environment's bin_dir contributes."""
    monkeypatch.delenv("PATH", raising=False)

    result = venv.build_env(None)

    assert result["PATH"] == str(venv.venv_path / venv_bin_dir)
