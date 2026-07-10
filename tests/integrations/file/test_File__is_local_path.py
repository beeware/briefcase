import os

import pytest


@pytest.mark.parametrize(
    ("path", "is_local"),
    [
        # Files and file-like things
        ("/path/to/file.txt", True),
        ("path/to/file.txt", True),
        # URLs
        ("http://example.com", False),
        ("https://example.com", False),
        ("git+https://github.com/example/repo", False),
    ],
)
def test_is_local_path(mock_tools, path, is_local):
    """Local paths can be identified."""
    assert mock_tools.file.is_local_path(path) == is_local


@pytest.mark.parametrize(
    ("altsep", "requirement", "expected"),
    [
        (None, "asdf/xcvb", True),
        (None, "asdf>xcvb", False),
        (">", "asdf/xcvb", True),
        (">", "asdf>xcvb", True),
        (">", "asdf+xcvb", False),
    ],
)
def test_altsep_respected(
    mock_tools,
    altsep,
    requirement,
    expected,
    monkeypatch,
):
    """`os.altsep` is included as a separator when available."""
    monkeypatch.setattr(os, "sep", "/")
    monkeypatch.setattr(os, "altsep", altsep)
    assert mock_tools.file.is_local_path(requirement) is expected
