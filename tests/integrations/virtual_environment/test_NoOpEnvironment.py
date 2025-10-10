from unittest.mock import MagicMock

from briefcase.integrations.virtual_environment import NoOpEnvironment


def test_init(mock_tools, dummy_console, marker_path):
    """NoOpEnvironment initialization sets correct attributes."""
    env = NoOpEnvironment(
        tools=mock_tools, console=dummy_console, marker_path=marker_path
    )

    assert env.tools == mock_tools
    assert env.console == dummy_console
    assert env.noop_context.marker_path == marker_path
    assert env.noop_context.tools == mock_tools


def test_noop_context_nonexistent_marker(mock_tools, dummy_console, tmp_path):
    """Context manager creates marker when it doesn't exist."""
    marker_path = tmp_path / "marker"
    env = NoOpEnvironment(
        tools=mock_tools, console=dummy_console, marker_path=marker_path
    )

    env.noop_context = MagicMock()
    env.noop_context.check_and_update_marker.return_value = True

    with env as context:
        assert context == env.noop_context
        env.noop_context.check_and_update_marker.assert_called_once()


def test_noop_context_existing_marker(mock_tools, dummy_console, tmp_path):
    """Context manager checks marker when it exists."""
    marker_path = tmp_path / "marker"
    env = NoOpEnvironment(
        tools=mock_tools, console=dummy_console, marker_path=marker_path
    )

    env.noop_context = MagicMock()
    env.noop_context.check_and_update_marker.return_value = False

    with env as context:
        assert context == env.noop_context
        env.noop_context.check_and_update_marker.assert_called_once()


def test_exception_handling(mock_tools, dummy_console, tmp_path):
    """Context manager handles exceptions properly."""
    marker_path = tmp_path / "marker"
    env = NoOpEnvironment(
        tools=mock_tools, console=dummy_console, marker_path=marker_path
    )

    env.noop_context = MagicMock()

    try:
        with env as context:
            assert context == env.noop_context
            raise ValueError("Test exception")
    except ValueError:
        pass

    env.noop_context.check_and_update_marker.assert_called_once()


def test_multiple_context_entries(mock_tools, dummy_console, tmp_path):
    """NoOpEnvironment can be entered multiple times."""
    marker_path = tmp_path / "marker"
    env = NoOpEnvironment(
        tools=mock_tools, console=dummy_console, marker_path=marker_path
    )

    env.noop_context = MagicMock()

    with env as context1:
        assert context1 == env.noop_context

    with env as context2:
        assert context2 == env.noop_context
        assert context2 == context1
