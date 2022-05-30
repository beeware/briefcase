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
    ],
)
def test_is_invalid_app_name(name):
    """Test that invalid app names are rejected."""
    assert not is_valid_app_name(name)
