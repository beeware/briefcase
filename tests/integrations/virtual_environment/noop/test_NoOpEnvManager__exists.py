from briefcase.integrations.virtual_environment import NoOpEnvManager


def test_exists(mock_tools, venv_path):
    """A No-Op environment always exists, even if the marker doesn't."""
    manager = NoOpEnvManager(mock_tools, venv_path)
    assert not manager.marker_path.exists()
    assert manager.exists() is True

    manager.prepare()

    # After preparation, the marker exists.
    assert manager.marker_path.exists()
    assert manager.exists() is True
