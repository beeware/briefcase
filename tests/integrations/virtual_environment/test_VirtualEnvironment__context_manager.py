from unittest.mock import MagicMock

from briefcase.integrations.virtual_environment import VenvEnvironment


def test_recreate_true(dummy_tools, dummy_console, tmp_path):
    """Test context manager recreates environment when recreate=True."""
    venv_path = tmp_path / "test_venv"
    env = VenvEnvironment(
        dummy_tools,
        dummy_console,
        path=venv_path,
        recreate=True,
    )

    env.venv_context.recreate = MagicMock()

    with env as context:
        assert context == env.venv_context
        env.venv_context.recreate.assert_called_once()


def test_recreate_true_exists(dummy_tools, dummy_console, tmp_path):
    """Test context manager recreates environment when recreate=True, even when venv
    exists."""
    venv_path = tmp_path / "test_venv"
    env = VenvEnvironment(
        dummy_tools,
        dummy_console,
        path=venv_path,
        recreate=True,
    )

    env.venv_context.exists = MagicMock(return_value=True)
    env.venv_context.recreate = MagicMock()
    env.venv_context.create = MagicMock()

    with env as context:
        assert context == env.venv_context
        env.venv_context.exists.assert_not_called()
        env.venv_context.recreate.assert_called_once()
        env.venv_context.create.assert_not_called()


def test_venv_nonexistent(dummy_tools, dummy_console, tmp_path):
    """Test context manager creates environment when it doesn't exist."""
    venv_path = tmp_path / "test_venv"
    env = VenvEnvironment(
        dummy_tools,
        dummy_console,
        path=venv_path,
        recreate=False,
    )

    env.venv_context.exists = MagicMock(return_value=False)
    env.venv_context.create = MagicMock()

    with env as context:
        assert context == env.venv_context
        env.venv_context.exists.assert_called_once()
        env.venv_context.create.assert_called_once()


def test_venv_exists(dummy_tools, dummy_console, tmp_path):
    """Test context manager does nothing when environment exists and recreate=False."""
    venv_path = tmp_path / "test_venv"
    env = VenvEnvironment(
        dummy_tools,
        dummy_console,
        path=venv_path,
        recreate=False,
    )

    env.venv_context.exists = MagicMock(return_value=True)
    env.venv_context.create = MagicMock()
    env.venv_context.recreate = MagicMock()

    with env as context:
        assert context == env.venv_context
        env.venv_context.exists.assert_called_once()
        env.venv_context.create.assert_not_called()
        env.venv_context.recreate.assert_not_called()


def test_exception_handling(dummy_tools, dummy_console, tmp_path):
    """Test context manager handles exceptions properly."""
    venv_path = tmp_path / "test_venv"
    env = VenvEnvironment(
        dummy_tools,
        dummy_console,
        path=venv_path,
        recreate=False,
    )

    env.venv_context.exists = MagicMock(return_value=True)

    try:
        with env as context:
            assert context == env.venv_context
            raise ValueError("Test exception")
    except ValueError:
        pass

    env.venv_context.exists.assert_called_once()
