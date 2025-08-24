import sys

import pytest

from briefcase.platforms.macOS import utils


@pytest.mark.skipif(sys.platform != "darwin", reason="Test runs only on macOS")
@pytest.mark.parametrize(
    "uti, result",
    [
        (None, False),
        ("com.unknown.data", False),
        ("public.data", True),
        ("public.content", True),
        ("com.adobe.pdf", True),
    ],
)
def test_is_uti_core_type(uti, result):
    """Check if a UTI is a core type."""
    assert utils.is_uti_core_type(uti) == result


@pytest.mark.skipif(sys.platform != "darwin", reason="Test runs only on macOS")
def test_is_uti_core_type_with_nonexisting_coretypes_file(monkeypatch):
    """Test that is_uti_core_type returns None if the coretypes file doesn't exist."""
    monkeypatch.setattr(utils, "CORETYPES_PATH", "/does/not/exist")
    assert utils.is_uti_core_type("com.adobe.pdf") is False
