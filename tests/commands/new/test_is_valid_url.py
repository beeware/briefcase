import pytest


@pytest.mark.parametrize(
    'url',
    [
        'https://example.com',
    ]
)
def test_valid_url(new_command, url):
    "Test that valid URLs are accepted"
    assert new_command.is_valid_url(url)


@pytest.mark.parametrize(
    'url',
    [
        'not a URL!',  # Free text.
    ]
)
def test_invalid_url(new_command, url):
    "Test that invalid URLs are rejected"
    with pytest.raises(ValueError):
        new_command.is_valid_url(url)
