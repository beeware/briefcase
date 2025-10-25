from unittest.mock import MagicMock


def test_run_passes_through_to_subprocess(noop_context, mock_noop_subprocess_setup):
    """Run passes all arguments to tools.subprocess.run."""
    mocks = mock_noop_subprocess_setup
    mock_result = MagicMock()
    mocks["subprocess"].run.return_value = mock_result

    args = ["python", "-m", "pip", "install", "package"]
    kwargs = {"check": True, "cwd": "/tmp", "env": {"PATH": "/usr/bin"}}

    result = noop_context.run(args, **kwargs)

    mocks["subprocess"].run.assert_called_once_with(args, **kwargs)
    assert result is mock_result


def test_run_with_no_kwargs(noop_context, mock_noop_subprocess_setup):
    """Run works with just args, no kwargs."""
    mocks = mock_noop_subprocess_setup
    mock_result = MagicMock()
    mocks["subprocess"].run.return_value = mock_result

    args = ["python", "--version"]
    result = noop_context.run(args)

    mocks["subprocess"].run.assert_called_once_with(args)
    assert result is mock_result


def test_run_preserves_original_kwargs(noop_context, mock_noop_subprocess_setup):
    """Run does not modify the original kwargs dict."""
    mocks = mock_noop_subprocess_setup
    mock_result = MagicMock()
    mocks["subprocess"].run.return_value = mock_result

    original_kwargs = {"check": True, "env": {"CUSTOM": "value"}}
    kwargs_copy = original_kwargs.copy()

    result = noop_context.run(["test"], **original_kwargs)

    assert original_kwargs == kwargs_copy
    mocks["subprocess"].run.assert_called_once_with(["test"], **original_kwargs)
    assert result is mock_result
