from ..conftest import MockVirtualEnvironment


def test_create(mock_tools, venv_path):
    """An environment can be created."""
    venv = MockVirtualEnvironment(mock_tools, venv_path)

    assert venv.created
    assert venv.exists()
    assert venv.tools == mock_tools
    assert venv.venv_path == venv_path
