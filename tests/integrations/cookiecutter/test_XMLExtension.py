from unittest.mock import MagicMock

import pytest

from briefcase.integrations.cookiecutter import XMLExtension


@pytest.mark.parametrize(
    "value, expected",
    [
        # Literal booleans
        (True, "true"),
        (False, "false"),
        # True-ish values
        (1, "true"),
        ("Hello", "true"),
        # False-ish values
        (0, "false"),
        ("", "false"),
    ],
)
def test_bool_attr(value, expected):
    env = MagicMock()
    env.filters = {}
    XMLExtension(env)
    assert env.filters["bool_attr"](value) == expected


@pytest.mark.parametrize(
    "value, expected",
    [
        # No special characters
        ("Hello World", "Hello World"),
        # Ampersands escaped
        ("Hello & World", "Hello &amp; World"),
        # Less than
        ("Hello < World", "Hello &lt; World"),
        # Greater than
        ("Hello > World", "Hello &gt; World"),
    ],
)
def test_xml_escape(value, expected):
    env = MagicMock()
    env.filters = {}
    XMLExtension(env)
    assert env.filters["xml_escape"](value) == expected


@pytest.mark.parametrize(
    "value, expected",
    [
        # A single quote wrapped in double quotes
        ("Hello ' World", '"Hello \' World"'),
        # A double quote wrapped in single quotes
        ('Hello " World', "'Hello \" World'"),
        # A double quote and a single quote in the same string value
        ("Hello \" And ' World", '"Hello &quot; And \' World"'),
    ],
)
def test_xml_attr(value, expected):
    env = MagicMock()
    env.filters = {}
    XMLExtension(env)
    assert env.filters["xml_attr"](value) == expected
