import pytest


@pytest.mark.parametrize(
    'bundle',
    [
        'com.example',
        'com.example.more',
        'com.example42.more',
        'com.example-42.more',
    ]
)
def test_valid_bundle(new_command, bundle):
    "Test that valid bundles are accepted"
    assert new_command.is_valid_bundle(bundle)


@pytest.mark.parametrize(
    'bundle',
    [
        'not a bundle!',  # Free text.
        'home',  # Only one section.
        'com.hello_world',  # underscore
        'com.hello,world',  # comma
        'com.hello world!',  # exclamation point
    ]
)
def test_invalid_bundle(new_command, bundle):
    "Test that invalid bundles are rejected"
    with pytest.raises(ValueError):
        new_command.is_valid_bundle(bundle)
