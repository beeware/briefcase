from briefcase.integrations.virtual_environment import NoOpEnvironment


def test_init(mock_tools, dummy_console):
    """NoOpEnvironment initialization."""
    env = NoOpEnvironment(tools=mock_tools, console=dummy_console)
    assert env.tools == mock_tools
    assert env.console == dummy_console


def test_context_manager(mock_tools, dummy_console):
    """NoOpEnvironment works as a context manager."""
    with NoOpEnvironment(tools=mock_tools, console=dummy_console) as venv:
        assert venv == mock_tools.subprocess
