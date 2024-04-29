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
        # İ and K (i.e. 0x212a) are valid ASCII when made lowercase and as such are
        # accepted by the PEP-508 regex...but these should be rejected here to ensure
        # compliance where app name is used downstream and only ASCII is accepted.
        "İstanbul",
        "Kelvin",
    ],
)
def test_is_invalid_app_name(name):
    """Test that invalid app names are rejected."""
    assert not is_valid_app_name(name)
