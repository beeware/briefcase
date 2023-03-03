import pytest

from briefcase.exceptions import ParseError
from briefcase.platforms.linux import parse_freedesktop_os_release


def test_parse():
    "Content can be parsed from a freedesktop file."
    content = """
KEY1=value
KEY2="quoted value"
KEY3 = value with spaces

KEY4=42
 KEY5 = "quoted value with spaces"
"""
    assert parse_freedesktop_os_release(content) == {
        "KEY1": "value",
        "KEY2": "quoted value",
        "KEY3": "value with spaces",
        "KEY4": "42",
        "KEY5": "quoted value with spaces",
    }


@pytest.mark.parametrize(
    "content, error",
    [
        (None, r"'NoneType' object has no attribute 'split'"),
        ("KEY=value\nnot valid content", r"list index out of range"),
    ],
)
def test_parse_error(content, error):
    with pytest.raises(
        ParseError,
        match=r"Failed to parse output of FreeDesktop os-release file: " + error,
    ):
        parse_freedesktop_os_release(content)
