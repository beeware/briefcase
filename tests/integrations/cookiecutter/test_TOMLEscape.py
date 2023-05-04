from unittest.mock import MagicMock

import pytest

from briefcase.integrations.cookiecutter import TOMLEscape


@pytest.mark.parametrize(
    "value, expected",
    [
        # Single digit minor
        ("Hello World", "Hello World"),
        ('Hello " World', 'Hello " World'),
        ("Hello \\ World", "Hello \\\\ World"),
    ],
)
def test_escape_toml(value, expected):
    env = MagicMock()
    env.filters = {}
    TOMLEscape(env)
    assert env.filters["escape_toml"](value) == expected


@pytest.mark.parametrize(
    "value, expected",
    [
        ("helloworld", "helloworld"),
        ("helloworldı", '"helloworldı"'),
    ],
)
def test_escape_non_ascii(value, expected):
    env = MagicMock()
    env.filters = {}
    TOMLEscape(env)
    assert env.filters["escape_non_ascii"](value) == expected
