import sys

import pytest

from briefcase.platforms.macOS import utils


@pytest.mark.skipif(sys.platform != "darwin", reason="Test runs only on macOS")
def test_mime_type_to_uti():
    """Check if a MIME type can be converted to a UTI."""
    assert utils.mime_type_to_uti(None) is None
    assert utils.mime_type_to_uti("application/pdf") == "com.adobe.pdf"
    assert utils.mime_type_to_uti("text/plain") == "public.plain-text"
    assert utils.mime_type_to_uti("image/png") == "public.png"
    assert utils.mime_type_to_uti("application/unknown") is None


@pytest.mark.skipif(sys.platform != "darwin", reason="Test runs only on macOS")
def test_mime_type_to_uti_with_nonexisting_coretypes_file(monkeypatch):
    """Test that mime_type_to_UTI returns None if the coretypes file doesn't exist."""
    monkeypatch.setattr(utils, "CORETYPES_PATH", "/does/not/exist")
    assert utils.mime_type_to_uti("application/pdf") is None
