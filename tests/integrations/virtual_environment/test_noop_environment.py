from briefcase.integrations.virtual_environment import NoOpEnvironment


def test_init(dummy_tools, dummy_console):
    """Test NoOpEnvironment initialization."""
    env = NoOpEnvironment(tools=dummy_tools, console=dummy_console)
    assert env.tools == dummy_tools
    assert env.console == dummy_console


def test_enter_returns_subprocess(dummy_tools, dummy_console):
    """Test __enter__ returns subprocess."""
    env = NoOpEnvironment(tools=dummy_tools, console=dummy_console)
    result = env.__enter__()
    assert result == dummy_tools.subprocess


def test_exit(dummy_tools, dummy_console):
    """Test __exit__ returns False."""
    env = NoOpEnvironment(tools=dummy_tools, console=dummy_console)
    assert env.__exit__(None, None, None) is False
