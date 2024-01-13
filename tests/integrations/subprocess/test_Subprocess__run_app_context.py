def test_run_app_context(mock_sub):
    """Run app context manager returns the input."""
    in_kwargs = object()
    with mock_sub.run_app_context(subprocess_kwargs=in_kwargs) as kwargs:
        assert in_kwargs is kwargs
