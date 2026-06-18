from briefcase.integrations.virtual_environment import NoOpVirtualEnvironment


def test_clean(mock_tools, venv_path):
    """The marker file is removed by a clean."""
    venv = NoOpVirtualEnvironment(mock_tools, venv_path)

    assert venv.marker_path.exists()

    venv.clean()
    assert not venv.marker_path.exists()

    # Cleaning a second time is a no-op
    venv.clean()
