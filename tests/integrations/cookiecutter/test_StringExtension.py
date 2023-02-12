from unittest.mock import MagicMock

import pytest

from briefcase.integrations.cookiecutter import StringExtension


@pytest.mark.parametrize(
    "value, expected",
    [
        ("", ""),
        ("Hello World", "Hello World"),
        ("Hello\nWorld", "Hello"),
    ],
)
def test_first_line(value, expected):
    env = MagicMock()
    env.filters = {}
    StringExtension(env)
    assert env.filters["first_line"](value) == expected


@pytest.mark.parametrize(
    "value, expected",
    [
        ("", ""),
        ("Hello World", "Hello World"),
        ("Hello\nWorld", "Hello\n World"),
        ("Hello\n\nWorld", "Hello\n World"),
        ("Hello\nWorld\n \nAgain", "Hello\n World\n Again"),
    ],
)
def test_multiline_description(value, expected):
    env = MagicMock()
    env.filters = {}
    StringExtension(env)
    assert env.filters["multiline_description"](value) == expected
