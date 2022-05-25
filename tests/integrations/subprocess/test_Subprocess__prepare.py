def test_build_image(mock_sub):
    """Building an image is a no-op."""

    mock_sub.prepare()

    assert mock_sub._subprocess.run.call_count == 0
