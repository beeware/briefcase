import pytest

from briefcase.config import is_valid_bundle_identifier


@pytest.mark.parametrize(
    'bundle',
    [
        'com.example',
        'com.example.more',
        'com.example42.more',
        'com.example-42.more',
    ]
)
def test_valid_bundle(bundle):
    "Test that valid bundles are accepted"
    assert is_valid_bundle_identifier(bundle)


@pytest.mark.parametrize(
    'bundle',
    [
        'not a bundle!',  # Free text.
        'home',  # Only one section.
        'com.hello_world',  # underscore
        'com.hello,world',  # comma
        'com.hello world!',  # exclamation point
        'com.pass',  # Python reserved word
        'com.pass.example',  # Python reserved word
        'com.switch',  # Java reserved word
        'com.switch.example',  # Java reserved word
    ]
)
def test_invalid_bundle(bundle):
    "Test that invalid bundles are rejected"
    assert not is_valid_bundle_identifier(bundle)
