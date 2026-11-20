from unittest.mock import MagicMock

import pytest

from briefcase.integrations.cookiecutter import TOMLEscape


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        # Single digit minor
        ("Hello World", "Hello World"),
        ('Hello " World', 'Hello \\" World'),
        ("Hello \\ World", "Hello \\\\ World"),
    ],
)
def test_escape_toml(value, expected):
    env = MagicMock()
    env.filters = {}
    TOMLEscape(env)
    assert env.filters["escape_toml"](value) == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("helloworld", "helloworld"),
        ("helloworldı", '"helloworldı"'),  # noqa: RUF001 (ambiguous non-ASCII symbol)
    ],
)
def test_escape_non_ascii(value, expected):
    env = MagicMock()
    env.filters = {}
    TOMLEscape(env)
    assert env.filters["escape_non_ascii"](value) == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        # An empty table
        ({}, "{}"),
        # A single key
        ({"name": "Jane Developer"}, '{name = "Jane Developer"}'),
        # Multiple keys preserve their order
        (
            {"name": "Jane Developer", "email": "jane@example.com"},
            '{name = "Jane Developer", email = "jane@example.com"}',
        ),
        # Values that need TOML escaping are escaped
        ({"name": 'Jane "JD" Developer'}, '{name = "Jane \\"JD\\" Developer"}'),
        ({"name": "Jane\\Developer"}, '{name = "Jane\\\\Developer"}'),
    ],
)
def test_toml_inline_table(value, expected):
    env = MagicMock()
    env.filters = {}
    TOMLEscape(env)
    assert env.filters["toml_inline_table"](value) == expected
