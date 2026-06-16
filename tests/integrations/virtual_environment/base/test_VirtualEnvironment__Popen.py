def test_noop(mock_tools, noop_venv, mock_POpen_instance):
    """A no-op environment doesn't alter anything."""
    return_value = noop_venv.Popen(["arg1", "arg2"], flag1=1, flag2=2)

    assert return_value == mock_POpen_instance
    mock_tools.subprocess.Popen.assert_called_once_with(
        ["arg1", "arg2"], flag1=1, flag2=2
    )


def test_no_env(mock_tools, mock_venv, mock_POpen_instance):
    """Popen with no environment still adds some env keys."""
    return_value = mock_venv.Popen(["arg1", "arg2"], flag1=1, flag2=2)

    assert return_value == mock_POpen_instance
    mock_tools.subprocess.Popen.assert_called_once_with(
        ["rewrite", "arg1", "arg2"], flag1=1, flag2=2, env={"VENV": "active"}
    )


def test_Popen(mock_tools, mock_venv, mock_POpen_instance):
    """Popen uses a modified environment."""

    return_value = mock_venv.Popen(
        ["arg1", "arg2"], flag1=1, flag2=2, env={"VAR": "value"}
    )

    assert return_value == mock_POpen_instance
    mock_tools.subprocess.Popen.assert_called_once_with(
        ["rewrite", "arg1", "arg2"],
        flag1=1,
        flag2=2,
        env={"VAR": "value", "VENV": "active"},
    )
