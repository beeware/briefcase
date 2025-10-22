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
    ],
)
def test_invalid_url(url):
    """Test that invalid URLs are rejected."""
    with pytest.raises(ValueError, match="Not a valid URL"):
        validate_url(url)


def test_invalid_website_url():
    """Test that non-website URLs are rejected."""
    with pytest.raises(ValueError, match="Not a valid website URL"):
        validate_url("gopher://example.com")  # URL, but not a webpage
