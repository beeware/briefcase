import pytest


@pytest.mark.parametrize(
    "name",
    [
        # Various forms of capitalization and alphanumeric
        "Hello World",
        "helloworld",
        "helloWorld",
        "hello42world",
        "42helloworld",
        # Names that include punctuation
        "hello_world",
        "hello-world",
        "_helloworld",
        "/helloworld",
        "Hello / World!",
        # Internationalized names that can be unicode-simplified
        "Hallo Vögel",
        "Bonjour Garçon",
        # Internationalized names that cannot be unicode-simplified
        "你好 世界!",
    ],
)
def test_valid_formal_name(new_command, name):
    """Test that valid formal names are accepted."""
    assert new_command.validate_formal_name(name)


@pytest.mark.parametrize(
    "name",
    [
        "",  # Empty
        " ",  # Just a space
        "\t",  # Other whitespace characters
        "/",  # Just a slash
        "'",
        "\\",
        "/'\\",  # Multiple invalid characters
    ],
)
def test_invalid_formal_name(new_command, name, tmp_path):
    """Test that invalid app names are rejected."""
    (tmp_path / "existing").mkdir()

    with pytest.raises(ValueError):
        new_command.validate_formal_name(name)
