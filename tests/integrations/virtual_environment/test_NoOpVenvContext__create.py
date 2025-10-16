import sys
from pathlib import Path


def test_creates_marker_when_missing(noop_context):
    """A marker file is created when it doesn't exist."""
    assert not noop_context.marker_path.exists()

    noop_context.create()

    assert noop_context.created is True
    assert noop_context.marker_path.exists()
    assert noop_context.marker_path.read_text(encoding="utf-8") == sys.executable


def test_returns_false_when_marker_unchanged(noop_context):
    """Environment is not marked as created when executable hasn't changed."""
    noop_context.marker_path.parent.mkdir(parents=True, exist_ok=True)
    noop_context.marker_path.write_text(sys.executable, encoding="utf-8")

    noop_context.create()

    assert noop_context.created is False
    assert noop_context.marker_path.read_text(encoding="utf-8") == sys.executable


def test_updates_marker_when_executable_changed(noop_context):
    """Create updates marker when executable changes."""
    noop_context.marker_path.parent.mkdir(parents=True, exist_ok=True)
    old_executable = "/old/python/path"
    noop_context.marker_path.write_text(old_executable, encoding="utf-8")

    noop_context.create()

    assert noop_context.created is True
    assert noop_context.marker_path.read_text(encoding="utf-8") == sys.executable
    assert noop_context.marker_path.read_text(encoding="utf-8") != old_executable


def test_handles_whitespace_in_marker(noop_context):
    """Create strips whitespace when reading marker."""
    noop_context.marker_path.parent.mkdir(parents=True, exist_ok=True)
    noop_context.marker_path.write_text(f"  {sys.executable}  \n", encoding="utf-8")

    noop_context.create()

    assert noop_context.created is False


def test_handles_oserror_during_read(noop_context, monkeypatch):
    """Create handles OSError by recreating marker."""
    noop_context.marker_path.parent.mkdir(parents=True, exist_ok=True)
    noop_context.marker_path.write_text("something", encoding="utf-8")

    original_read = Path.read_text

    def mock_read_text(*args, **kwargs):
        raise OSError("Permission denied")

    monkeypatch.setattr(Path, "read_text", mock_read_text)

    noop_context.create()

    assert noop_context.created is True

    monkeypatch.setattr(Path, "read_text", original_read)
    assert noop_context.marker_path.read_text(encoding="utf-8") == sys.executable


def test_handles_unicode_decode_error(noop_context):
    """Create handles UnicodeDecodeError by recreating marker."""
    noop_context.marker_path.parent.mkdir(parents=True, exist_ok=True)
    noop_context.marker_path.write_bytes(b"\xff\xfe\xfd")

    noop_context.create()

    assert noop_context.created is True
    assert noop_context.marker_path.read_text(encoding="utf-8") == sys.executable


def test_marker_persists_across_instances(mock_tools, tmp_path):
    """Marker file persists and is readable by new instances."""
    from briefcase.integrations.virtual_environment import NoOpVenvContext

    venv_path = tmp_path / "venv"

    context1 = NoOpVenvContext(tools=mock_tools, venv_path=venv_path)
    context1.create()
    assert context1.created is True

    context2 = NoOpVenvContext(tools=mock_tools, venv_path=venv_path)
    context2.create()
    assert context2.created is False
