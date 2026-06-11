import sys
from pathlib import Path

import pytest

from briefcase.integrations.virtual_environment import NoOpEnvManager


@pytest.mark.parametrize("recreate", [True, False])
def test_existing(mock_tools, venv_path, recreate):
    """If the environment matches, prepare is a no-op."""
    manager = NoOpEnvManager(mock_tools, venv_path)
    manager.marker_path.parent.mkdir(parents=True, exist_ok=True)
    manager.marker_path.write_text(sys.executable, encoding="utf-8")

    result = manager.prepare(recreate=recreate)

    # If a recreate was requested, that is reflected in the result
    assert result is recreate
    assert manager.marker_path.read_text(encoding="utf-8") == sys.executable


@pytest.mark.parametrize("recreate", [True, False])
def test_environment_change(mock_tools, venv_path, recreate):
    """If the environment marker exists, but doesn't match, marker is re-written."""
    manager = NoOpEnvManager(mock_tools, venv_path)
    manager.marker_path.parent.mkdir(parents=True, exist_ok=True)
    manager.marker_path.write_text("Something else", encoding="utf-8")

    result = manager.prepare(recreate=recreate)

    # A change in environment is always a recreate
    assert result is True
    assert manager.marker_path.read_text(encoding="utf-8") == sys.executable


def test_prepare_creates_parent_directory(mock_tools, tmp_path):
    """Parent directories for the marker file are created on demand."""
    venv = tmp_path / "deep" / "missing" / "venv"
    manager = NoOpEnvManager(mock_tools, venv)

    result = manager.prepare()

    assert result is True
    assert manager.marker_path.is_file()


def test_strip_whitespace_from_marker(mock_tools, venv_path):
    """A marker file with trailing whitespace still matches sys.executable."""
    manager = NoOpEnvManager(mock_tools, venv_path)
    manager.marker_path.parent.mkdir(parents=True, exist_ok=True)
    manager.marker_path.write_text(f"  {sys.executable}  \n", encoding="utf-8")

    result = manager.prepare()

    assert result is False


def test_handles_oserror(mock_tools, venv_path, monkeypatch):
    """If the marker can't be read, the environment is re-created."""
    manager = NoOpEnvManager(mock_tools, venv_path)
    manager.marker_path.parent.mkdir(parents=True, exist_ok=True)
    manager.marker_path.write_text("anything", encoding="utf-8")

    original_read = Path.read_text

    def boom(*args, **kwargs):
        raise OSError("Permission denied")

    monkeypatch.setattr(Path, "read_text", boom)
    result = manager.prepare()

    assert result is True
    monkeypatch.setattr(Path, "read_text", original_read)
    assert manager.marker_path.read_text(encoding="utf-8") == sys.executable


def test_handles_unicode_decode_error(mock_tools, venv_path):
    """If the marker has bad encoding, it is re-written."""
    manager = NoOpEnvManager(mock_tools, venv_path)
    manager.marker_path.parent.mkdir(parents=True, exist_ok=True)
    manager.marker_path.write_bytes(b"\xff\xfe\xfd")

    result = manager.prepare()

    assert result is True
    assert manager.marker_path.read_text(encoding="utf-8") == sys.executable
