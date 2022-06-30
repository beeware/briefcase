import pytest

from briefcase.config import is_valid_url


@pytest.mark.parametrize(
    "url",
    [
        "https://www.example.com/",
        "https://example.com/",
        "http://www.example.com/",
        "https://www.example.com/plugin.AppImage",
        "http://www.example.net/bedroom/plugin.sh",
        "https://www.example.com/plugin.AppImage",
    ],
)
def test_is_valid_url(url):
    """Test that valid URLs are accepted."""
    assert is_valid_url(url)


@pytest.mark.parametrize(
    "url",
    [
        "C:/Users/brutus/briefcase",
        "/home/brutus/briefcase/test.sh",
        "example",
        "plugin.AppImage",
        "plugin.sh",
    ],
)
def test_not_valid_url(url):
    assert not is_valid_url(url)
