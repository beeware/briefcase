import pytest

from briefcase.config import is_valid_app_name


@pytest.mark.parametrize(
    "name",
    [
        "helloworld",
        "helloWorld",
        "hello42world",
        "hello_world",
        "hello-world",
        "helloworld42",
        "a",  # single letter
        "abc123",  # alphanumeric
        "none",  # daft but legal ;-)
        "helloworld_",  # ends with underscore (valid Python identifier)
        "helloworld-",  # ends with hyphen (converts to valid identifier)
    ],
)
def test_is_valid_app_name(name):
    """Test that valid app names are accepted."""
    assert is_valid_app_name(name)


@pytest.mark.parametrize(
    "name",
    [
        # Invalid characters
        "hello world",
        "helloworld!",
        "_helloworld",
        "-helloworld",
        # python reserved words
        "switch",
        "pass",
        "false",
        "False",
        "YIELD",
        "main",
        "socket",
        "test",
        "None",
        # Additional invalid formats
        "my$app",  # dollar sign
        "app@domain",  # at symbol
        "app.name",  # period
        "2app",  # starts with number
        "42app",  # starts with number
        "_",  # single underscore
        "-",  # single hyphen
        "1",  # single digit
        "123",  # all digits
        # ı, İ and K (i.e. 0x212a) are valid ASCII when made lowercase and as such are
        # accepted by the official PEP 508 regex... but they are rejected here to ensure
        # compliance with the regex that is used in practice.
        "helloworld_ı",
        "İstanbul",
        "Kelvin",
        # Case variations of reserved words
        "Switch",
        "SWITCH",
        "FALSE",
        "Pass",
        "PASS",
        "Test",
        "TEST",
    ],
)
def test_is_invalid_app_name(name):
    """Test that invalid app names are rejected."""
    assert not is_valid_app_name(name)
