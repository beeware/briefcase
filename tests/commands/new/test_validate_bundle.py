import pytest


@pytest.mark.parametrize(
    "bundle",
    [
        "com.example",
        "com.example.more",
        "com.example42.more",
        "com.example-42.more",
        "ca.example.issue1212",
        "au.example.issue1212",
        "in.example.issue1212",
        "im.glyph.and.this.is.1212",
    ],
)
def test_valid_bundle(new_command, bundle):
    """Test that valid bundles are accepted."""
    assert new_command.validate_bundle(bundle)


@pytest.mark.parametrize(
    "bundle",
    [
        "not a bundle!",  # Free text.
        "home",  # Only one section.
        "com.hello_world",  # underscore
        "com.hello,world",  # comma
        "com.hello world!",  # exclamation point
    ],
)
def test_invalid_bundle(new_command, bundle):
    """Test that invalid bundles are rejected."""
    with pytest.raises(ValueError, match="is not a valid bundle identifier"):
        new_command.validate_bundle(bundle)
