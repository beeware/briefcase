import pytest

from briefcase.config import validate_url


@pytest.mark.parametrize(
    "url",
    [
        "https://example.com",
    ],
)
def test_valid_url(url):
    """Test that valid URLs are accepted."""
    assert validate_url(url)


@pytest.mark.parametrize(
    "url",
    [
        "not a URL!",  # Free text.
        "file:///usr/local/bin",  # File URL
        "gopher://example.com",  # URL, but not a webpage.
    ],
)
def test_invalid_url(url):
    """Test that invalid URLs are rejected."""
    with pytest.raises(ValueError):
        validate_url(url)
