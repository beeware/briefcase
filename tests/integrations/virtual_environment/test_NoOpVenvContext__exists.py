def test_exists_always_returns_true(noop_context):
    """Exists always returns True for no-op context."""
    assert noop_context.exists() is True


def test_exists_when_marker_missing(noop_context):
    """Exists returns True even when marker file doesn't exist."""
    assert not noop_context.marker_path.exists()
    assert noop_context.exists() is True
