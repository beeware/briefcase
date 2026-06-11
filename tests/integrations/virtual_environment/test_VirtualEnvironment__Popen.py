from briefcase.integrations.virtual_environment import VirtualEnvironment


def test_noop(mock_tools, noop_manager, process):
    """A no-op manager doesn't alter anything."""
    venv = VirtualEnvironment(mock_tools, noop_manager)

    return_value = venv.Popen(["arg1", "arg2"], flag1=1, flag2=2)

    assert return_value == process
    mock_tools.subprocess.Popen.assert_called_once_with(
        ["arg1", "arg2"], flag1=1, flag2=2
    )


def test_noop_with_env(mock_tools, noop_manager, process):
    """A no-op manager doesn't alter anything in the environment."""
    venv = VirtualEnvironment(mock_tools, noop_manager)

    return_value = venv.Popen(["arg1", "arg2"], flag1=1, flag2=2, env={"VAR": "value"})

    assert return_value == process
    mock_tools.subprocess.Popen.assert_called_once_with(
        ["arg1", "arg2"], flag1=1, flag2=2, env={"VAR": "value"}
    )


def test_simple_env(mock_tools, simple_manager, process):
    """A simple manager will alter args and environment."""
    venv = VirtualEnvironment(mock_tools, simple_manager)

    return_value = venv.Popen(["arg1", "arg2"], flag1=1, flag2=2, env={"VAR": "value"})

    assert return_value == process
    mock_tools.subprocess.Popen.assert_called_once_with(
        ["rewrite", "arg1", "arg2"],
        flag1=1,
        flag2=2,
        env={"VAR": "value", "VENV": "active"},
    )
