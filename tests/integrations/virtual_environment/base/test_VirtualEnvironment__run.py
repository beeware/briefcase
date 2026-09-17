def test_noop(mock_tools, noop_venv):
    """A no-op environment doesn't alter anything."""
    return_value = noop_venv.run(["arg1", "arg2"], flag1=1, flag2=2)

    assert return_value == 42
    mock_tools.subprocess.run.assert_called_once_with(
        ["arg1", "arg2"], flag1=1, flag2=2
    )


def test_no_env(mock_tools, mock_venv):
    """Run with no environment still adds some env keys."""
    return_value = mock_venv.run(["arg1", "arg2"], flag1=1, flag2=2)

    assert return_value == 42
    mock_tools.subprocess.run.assert_called_once_with(
        ["rewrite", "arg1", "arg2"], flag1=1, flag2=2, env={"VENV": "active"}
    )


def test_run(mock_tools, mock_venv):
    """Run uses a modified environment."""

    return_value = mock_venv.run(
        ["arg1", "arg2"], flag1=1, flag2=2, env={"VAR": "value"}
    )

    assert return_value == 42
    mock_tools.subprocess.run.assert_called_once_with(
        ["rewrite", "arg1", "arg2"],
        flag1=1,
        flag2=2,
        env={"VAR": "value", "VENV": "active"},
    )
