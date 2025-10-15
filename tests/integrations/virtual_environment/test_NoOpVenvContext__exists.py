def test_exists_always_returns_true(noop_context):
    """Exists always returns True for no-op context, regardless of marker state."""
    # Test when marker doesn't exist
    assert not noop_context.marker_path.exists()
    assert noop_context.exists() is True

    # Test when marker does exist
    noop_context.marker_path.parent.mkdir(parents=True, exist_ok=True)
    noop_context.marker_path.write_text("something", encoding="utf-8")
    assert noop_context.exists() is True
