import pytest


@pytest.mark.parametrize(
    "url",
    [
        "https://example.com",
    ],
)
def test_valid_url(new_command, url):
    """Test that valid URLs are accepted."""
    assert new_command.validate_url(url)


@pytest.mark.parametrize(
    "url",
    [
        "not a URL!",  # Free text.
        "file:///usr/local/bin",  # File URL
        "gopher://example.com",  # URL, but not a webpage.
    ],
)
def test_invalid_url(new_command, url):
    """Test that invalid URLs are rejected."""
    with pytest.raises(ValueError):
        new_command.validate_url(url)
