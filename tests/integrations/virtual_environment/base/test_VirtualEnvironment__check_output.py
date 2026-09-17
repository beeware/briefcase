def test_noop(mock_tools, noop_venv):
    """A no-op environment doesn't alter anything."""
    return_value = noop_venv.check_output(["arg1", "arg2"], flag1=1, flag2=2)

    assert return_value == "command output"
    mock_tools.subprocess.check_output.assert_called_once_with(
        ["arg1", "arg2"], flag1=1, flag2=2
    )


def test_no_env(mock_tools, mock_venv):
    """check_output with no environment still adds some env keys."""
    return_value = mock_venv.check_output(["arg1", "arg2"], flag1=1, flag2=2)

    assert return_value == "command output"
    mock_tools.subprocess.check_output.assert_called_once_with(
        ["rewrite", "arg1", "arg2"], flag1=1, flag2=2, env={"VENV": "active"}
    )


def test_check_output(mock_tools, mock_venv):
    """check_output uses a modified environment."""

    return_value = mock_venv.check_output(
        ["arg1", "arg2"], flag1=1, flag2=2, env={"VAR": "value"}
    )

    assert return_value == "command output"
    mock_tools.subprocess.check_output.assert_called_once_with(
        ["rewrite", "arg1", "arg2"],
        flag1=1,
        flag2=2,
        env={"VAR": "value", "VENV": "active"},
    )
