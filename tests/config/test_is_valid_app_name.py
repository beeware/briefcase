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
        "42helloworld",
        # ı, İ and K (i.e. 0x212a) are valid ASCII when made lowercase # noqa: RUF003
        # and as such are accepted by the official PEP 508 regex. They are rejected
        # here to ensure compliance with the regex that is used in practice.
        "helloworld_ı",  # noqa: RUF001 (ambiguous non-ASCII symbol)
        "İstanbul",
        "Kelvin",  # noqa: RUF001 (ambiguous non-ASCII symbol)
    ],
)
def test_is_invalid_app_name(name):
    """Test that invalid app names are rejected."""
    assert not is_valid_app_name(name)

@pytest.mark.parametrize(
    "app_name",
    [
        "my@app",
        "app#name",
        "hello$world",
        "test!app",
    ],
)
def test_invalid_app_name_special_characters(app_name):
    """Verify that app names with special characters are considered invalid."""
    assert not is_valid_app_name(app_name)