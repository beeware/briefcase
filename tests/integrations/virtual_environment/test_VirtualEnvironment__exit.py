from briefcase.integrations.virtual_environment import VenvEnvironment


class TestVirtualEnvironmentExit:
    """Tests for VenvEnvironment.__exit__ method."""

    def test_exit_returns_false(self, dummy_tools, dummy_console, tmp_path):
        """Test __exit__ returns False."""
        venv_path = tmp_path / "test_venv"
        env = VenvEnvironment(
            dummy_tools,
            dummy_console,
            path=venv_path,
            recreate=False,
        )

        result = env.__exit__(None, None, None)

        assert result is False
