def test_check_output_passes_through_to_subprocess(
    noop_context,
    mock_noop_subprocess_setup,
):
    """check_output passes all arguments to tools.subprocess.check_output."""
    mocks = mock_noop_subprocess_setup
    mock_output = "Python 3.10.0"
    mocks["subprocess"].check_output.return_value = mock_output

    args = ["python", "--version"]
    kwargs = {"encoding": "utf-8", "check": True}

    result = noop_context.check_output(args, **kwargs)

    mocks["subprocess"].check_output.assert_called_once_with(args, **kwargs)
    assert result == mock_output


def test_check_output_with_no_kwargs(noop_context, mock_noop_subprocess_setup):
    """check_output works with just args, no kwargs."""
    mocks = mock_noop_subprocess_setup
    mock_output = "output"
    mocks["subprocess"].check_output.return_value = mock_output

    args = ["echo", "test"]
    result = noop_context.check_output(args)

    mocks["subprocess"].check_output.assert_called_once_with(args)
    assert result == mock_output


def test_check_output_preserves_original_kwargs(
    noop_context,
    mock_noop_subprocess_setup,
):
    """check_output does not modify the original kwargs dict."""
    mocks = mock_noop_subprocess_setup
    mock_output = "output"
    mocks["subprocess"].check_output.return_value = mock_output

    original_kwargs = {"encoding": "utf-8", "env": {"CUSTOM": "value"}}
    kwargs_copy = original_kwargs.copy()

    result = noop_context.check_output(["test"], **original_kwargs)

    assert original_kwargs == kwargs_copy
    mocks["subprocess"].check_output.assert_called_once_with(
        ["test"], **original_kwargs
    )
    assert result == mock_output
