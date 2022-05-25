import pytest


@pytest.mark.parametrize(
    "name",
    [
        "helloworld",
        "helloWorld",
        "hello42world",
        "42helloworld",  # ?? Are we sure this is correct?
        "hello_world",
        "hello-world",
    ],
)
def test_valid_app_name(new_command, name):
    """Test that valid app names are accepted."""
    assert new_command.validate_app_name(name)


@pytest.mark.parametrize(
    "name",
    [
        "hello world",  # contains a space
        "helloworld!",  # contains punctuation
        "_helloworld",  # leading underscore
        "-helloworld",  # leading hyphen
        "pass",  # python keyword
        "Pass",  # python keyword, but different case usage
        "PASS",  # python keyword, but all upper case
        "in",  # javascript keyword
        "In",  # javascript keyword, but different case usage
        "IN",  # javascript keyword, but all upper case
        "synchronized",  # Java keyword
        "Synchronized",  # Java keyword, but different case usage
        "SYNCHRONIZED",  # Java keyword, but all upper case
        "false",  # Python, Java and Javascript keyword (in different cases)
        "False",  # Python, Java and Javascript keyword (in different cases)
        "FALSE",  # Python, Java and Javascript keyword (in different cases)
        "existing",  # pre-existing directory name
    ],
)
def test_invalid_app_name(new_command, name, tmp_path):
    """Test that invalid app names are rejected."""
    (tmp_path / "existing").mkdir()

    with pytest.raises(ValueError):
        new_command.validate_app_name(name)
