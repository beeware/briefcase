from unittest.mock import MagicMock

from briefcase.integrations.virtual_environment import NoOpEnvironment


def test_init(mock_tools, venv_path):
    """NoOpEnvironment initialization sets correct attributes."""
    env = NoOpEnvironment(
        tools=mock_tools,
        path=venv_path,
        recreate=True,
    )

    assert env.tools == mock_tools
    assert env.path == venv_path
    assert env.recreate is True

    assert env.noop_context.venv_path == venv_path
    assert env.noop_context.marker_path == venv_path / "venv_path"
    assert env.noop_context.tools == mock_tools


def test_noop_context_nonexistent_marker(mock_tools, tmp_path):
    """Context manager creates marker when it doesn't exist."""
    venv_path = tmp_path / "venv"
    env = NoOpEnvironment(
        tools=mock_tools,
        path=venv_path,
        recreate=False,
    )

    with env as context:
        assert context == env.noop_context
        assert context.created


def test_noop_context_existing_marker(mock_tools, tmp_path):
    """Context manager checks marker when it exists."""
    venv_path = tmp_path / "venv"

    # Force creation of an environment by explicitly calling create.
    NoOpEnvironment(
        tools=mock_tools,
        path=venv_path,
        recreate=False,
    ).noop_context.create()

    # Create a second instance of the same environment
    env = NoOpEnvironment(
        tools=mock_tools,
        path=venv_path,
        recreate=False,
    )

    with env as context:
        assert context == env.noop_context
        assert not context.created


def test_noop_context_existing_marker_with_recreate(mock_tools, tmp_path):
    """A request to recreate supersedes any marker file handling."""
    venv_path = tmp_path / "venv"

    # Force creation of an environment by explicitly calling create.
    NoOpEnvironment(
        tools=mock_tools,
        path=venv_path,
        recreate=False,
    ).noop_context.create()

    # Create a second instance of the same environment, but with recreate
    env = NoOpEnvironment(
        tools=mock_tools,
        path=venv_path,
        recreate=True,
    )

    with env as context:
        assert context == env.noop_context
        assert context.created


def test_exception_handling(mock_tools, tmp_path):
    """Context manager handles exceptions properly."""
    venv_path = tmp_path / "venv"
    env = NoOpEnvironment(
        tools=mock_tools,
        path=venv_path,
        recreate=False,
    )

    try:
        with env as context:
            assert context == env.noop_context
            raise ValueError("Test exception")
    except ValueError:
        pass


def test_multiple_context_entries(mock_tools, tmp_path):
    """NoOpEnvironment can be entered multiple times."""
    venv_path = tmp_path / "venv"
    env = NoOpEnvironment(
        tools=mock_tools,
        path=venv_path,
        recreate=False,
    )

    env.noop_context = MagicMock()

    with env as context1:
        assert context1 == env.noop_context

    with env as context2:
        assert context2 == env.noop_context
        assert context2 == context1
