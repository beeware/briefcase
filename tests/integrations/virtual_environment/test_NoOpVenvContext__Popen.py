from unittest.mock import MagicMock


def test_popen_passes_through_to_subprocess(noop_context, mock_noop_subprocess_setup):
    """Popen passes all arguments to tools.subprocess.Popen."""
    mocks = mock_noop_subprocess_setup
    mock_popen = MagicMock()
    mocks["subprocess"].Popen.return_value = mock_popen

    args = ["python", "-c", "print('hello')"]
    kwargs = {"stdout": "PIPE", "stderr": "PIPE", "env": {"TEST": "value"}}

    result = noop_context.Popen(args, **kwargs)

    mocks["subprocess"].Popen.assert_called_once_with(args, **kwargs)
    assert result is mock_popen


def test_popen_with_no_kwargs(noop_context, mock_noop_subprocess_setup):
    """Popen works with just args, no kwargs."""
    mocks = mock_noop_subprocess_setup
    mock_popen = MagicMock()
    mocks["subprocess"].Popen.return_value = mock_popen

    args = ["python", "-V"]
    result = noop_context.Popen(args)

    mocks["subprocess"].Popen.assert_called_once_with(args)
    assert result is mock_popen


def test_popen_preserves_original_kwargs(noop_context, mock_noop_subprocess_setup):
    """Popen does not modify the original kwargs dict."""
    mocks = mock_noop_subprocess_setup
    mock_popen = MagicMock()
    mocks["subprocess"].Popen.return_value = mock_popen

    original_kwargs = {"stdout": "PIPE", "env": {"CUSTOM": "value"}}
    kwargs_copy = original_kwargs.copy()

    result = noop_context.Popen(["test"], **original_kwargs)

    assert original_kwargs == kwargs_copy
    mocks["subprocess"].Popen.assert_called_once_with(["test"], **original_kwargs)
    assert result is mock_popen
