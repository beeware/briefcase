from unittest.mock import MagicMock

import pytest

from briefcase.integrations.cookiecutter import XMLExtension


@pytest.mark.parametrize(
    ("value", "expected"),
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
    ("value", "expected"),
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
    ("value", "expected"),
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


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        # Empty string
        ("", ""),
        # No special characters
        ("https://example.com/path", "https://example.com/path"),
        # Query strings, fragments and existing percent-encoding are preserved
        (
            "https://example.com/a?b=1&c=%41#frag",
            "https://example.com/a?b=1&c=%41#frag",
        ),
        # Square brackets and single quotes are not encoded
        ("https://example.com/?a[]=1&b='x'", "https://example.com/?a[]=1&b='x'"),
        # Double quotes are encoded
        ('https://example.com/?q="x"', "https://example.com/?q=%22x%22"),
        # Angle brackets are encoded
        ("https://example.com/<x>", "https://example.com/%3Cx%3E"),
        # Whitespace is encoded
        (
            "https://example.com/a b\tc\nd",
            "https://example.com/a%20b%09c%0Ad",
        ),
        # Non-ASCII whitespace is encoded as UTF-8 bytes
        ("https://example.com/a\u00a0b", "https://example.com/a%C2%A0b"),
        # Non-whitespace non-ASCII characters are not encoded
        (
            "https://example.com/caf\u00e9",  # codespell:ignore caf
            "https://example.com/caf\u00e9",  # codespell:ignore caf
        ),
    ],
)
def test_link_url(value, expected):
    env = MagicMock()
    env.filters = {}
    XMLExtension(env)
    assert env.filters["link_url"](value) == expected
