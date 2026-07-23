def test_clean(noop_venv, first_app, mock_tools):
    """The marker file is removed by a clean."""

    # a no-ope environment always exists, but the marker file won't
    assert noop_venv.exists()
    assert not noop_venv.marker_path.exists()

    # Marker path is created by preparing the environment
    noop_venv.prepare()
    assert noop_venv.exists()
    assert noop_venv.marker_path.exists()

    # Cleaning removes the marker file.
    noop_venv.clean()
    assert noop_venv.exists()
    assert not noop_venv.marker_path.exists()

    # Cleaning a second time is a no-op
    noop_venv.clean()
    assert noop_venv.exists()
    assert not noop_venv.marker_path.exists()
