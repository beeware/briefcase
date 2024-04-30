import pytest

from briefcase.config import is_valid_app_name


@pytest.mark.parametrize(
    "name",
    [
        "helloworld",
        "helloWorld",
        "hello42world",
        "42helloworld",
        "hello_world",
        "hello-world",
    ],
)
def test_is_valid_app_name(name):
    """Test that valid app names are accepted."""
    assert is_valid_app_name(name)


@pytest.mark.parametrize(
    "name",
    [
        "hello world",
        "helloworld!",
        "_helloworld",
        "-helloworld",
        "switch",
        "pass",
        "false",
        "False",
        "YIELD",
        "main",
        "socket",
        "test",
        # ı, İ and K (i.e. 0x212a) are valid ASCII when made lowercase and as such are
        # accepted by the official PEP 508 regex... but they are rejected here to ensure
        # compliance with the regex that is used in practice.
        "helloworld_ı",
        "İstanbul",
        "Kelvin",
    ],
)
def test_is_invalid_app_name(name):
    """Test that invalid app names are rejected."""
    assert not is_valid_app_name(name)
