from unittest.mock import MagicMock

from briefcase.integrations.virtual_environment import VenvEnvironment


class TestVirtualEnvironmentEnter:
    """Tests for the __enter__ method in VenvEnvironment."""

    # recreate true, exists false
    def test_enter_recreate_true(self, dummy_tools, dummy_console, tmp_path):
        """Test __enter__ recreates environment when recreate=True."""
        venv_path = tmp_path / "test_venv"
        env = VenvEnvironment(
            dummy_tools,
            dummy_console,
            path=venv_path,
            recreate=True,
        )

        env.venv_context.recreate = MagicMock()

        dummy_console.wait_bar = MagicMock()
        dummy_console.wait_bar.return_value.__enter__ = MagicMock()
        dummy_console.wait_bar.return_value.__exit__ = MagicMock(return_value=False)

        result = env.__enter__()

        dummy_console.wait_bar.assert_called_once_with(
            "Recreating virtual environment..."
        )
        env.venv_context.recreate.assert_called_once()

        assert result == env.venv_context

    # recreate true exists true
    def test_enter_recreate_true_exists(self, dummy_tools, dummy_console, tmp_path):
        """Test __enter__ recreates environment when recreate=True, when venv exists."""
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

        dummy_console.wait_bar = MagicMock()
        dummy_console.wait_bar.return_value.__enter__ = MagicMock()
        dummy_console.wait_bar.return_value.__exit__ = MagicMock(return_value=False)

        result = env.__enter__()

        env.venv_context.exists.assert_not_called()
        env.venv_context.recreate.assert_called_once()
        env.venv_context.create.assert_not_called()
        dummy_console.wait_bar.assert_called_once_with(
            "Recreating virtual environment..."
        )

        assert result == env.venv_context

    # recreate false, exists false
    def test_enter_venv_nonexistent(self, dummy_tools, dummy_console, tmp_path):
        """Test __enter__ creates environment when it doesn't exist."""
        venv_path = tmp_path / "test_venv"
        env = VenvEnvironment(
            dummy_tools,
            dummy_console,
            path=venv_path,
            recreate=False,
        )

        env.venv_context.exists = MagicMock(return_value=False)
        env.venv_context.create = MagicMock()

        dummy_console.wait_bar = MagicMock()
        dummy_console.wait_bar.return_value.__enter__ = MagicMock()
        dummy_console.wait_bar.return_value.__exit__ = MagicMock(return_value=False)

        result = env.__enter__()

        env.venv_context.exists.assert_called_once()

        dummy_console.wait_bar.assert_called_once_with(
            f"Creating virtual environment at {venv_path}..."
        )
        env.venv_context.create.assert_called_once()

        assert result == env.venv_context

    # recreate false, exists true
    def test_enter_venv_exists(self, dummy_tools, dummy_console, tmp_path):
        """Test __enter__ does nothing when environment exists and recreate=False."""
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

        result = env.__enter__()
        env.venv_context.exists.assert_called_once()
        env.venv_context.create.assert_not_called()
        env.venv_context.recreate.assert_not_called()
        dummy_console.wait_bar.assert_not_called()

        assert result == env.venv_context
