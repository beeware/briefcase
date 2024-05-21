import pytest


@pytest.mark.parametrize(
    "name",
    [
        "helloworld",
        "helloWorld",
        "hello42world",
        "42helloworld",
        "hello_world",
        "hello-world",
        "_helloworld",
        "/helloworld",
    ],
)
def test_valid_formal_name(new_command, name):
    """Test that valid formal names are accepted."""
    assert new_command.validate_formal_name(name)


@pytest.mark.parametrize(
    "name",
    [
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
