import sys

import pytest

from briefcase.platforms.macOS import utils


@pytest.mark.skipif(sys.platform != "darwin", reason="Test runs only on macOS")
@pytest.mark.parametrize(
    "mime_type, uti",
    [
        (None, None),
        ("application/pdf", "com.adobe.pdf"),
        ("text/plain", "public.plain-text"),
        ("image/png", "public.png"),
        ("application/unknown", None),
    ],
)
def test_mime_type_to_uti(mime_type, uti):
    """Check if a MIME type can be converted to a UTI."""
    assert utils.mime_type_to_uti(mime_type) == uti


@pytest.mark.skipif(sys.platform != "darwin", reason="Test runs only on macOS")
def test_mime_type_to_uti_with_nonexisting_coretypes_file(monkeypatch):
    """Test that mime_type_to_UTI returns None if the coretypes file doesn't exist."""
    monkeypatch.setattr(utils, "CORETYPES_PATH", "/does/not/exist")
    assert utils.mime_type_to_uti("application/pdf") is None
