import pytest

from briefcase.commands.base import parse_config_overrides
from briefcase.exceptions import BriefcaseCommandError


@pytest.mark.parametrize(
    "overrides, values",
    [
        # No content
        (None, {}),
        ([], {}),
        # Boolean
        (["key=true"], {"key": True}),
        # Integers
        (["key=42"], {"key": 42}),
        (["key=-42"], {"key": -42}),
        # Integers
        (["key=42.37"], {"key": 42.37}),
        (["key=-42.37"], {"key": -42.37}),
        # Strings
        (["key='hello'"], {"key": "hello"}),
        (["key=''"], {"key": ""}),
        (["key='42'"], {"key": "42"}),
        (['key="hello"'], {"key": "hello"}),
        (['key=""'], {"key": ""}),
        (['key="42"'], {"key": "42"}),
        # List
        (['key=[1, "two", true]'], {"key": [1, "two", True]}),
        # Dictionary
        (['key={a=1, b="two", c=true}'], {"key": {"a": 1, "b": "two", "c": True}}),
        # Multiple values
        (
            [
                "key1=42",
                'key2="hello"',
                'key3=[1, "two", true]',
                'key4={a=1, b="two", c=true}',
            ],
            {
                "key1": 42,
                "key2": "hello",
                "key3": [1, "two", True],
                "key4": {"a": 1, "b": "two", "c": True},
            },
        ),
    ],
)
def test_valid_overrides(overrides, values):
    """Valid values can be parsed as config overrides."""
    assert parse_config_overrides(overrides) == values


@pytest.mark.parametrize(
    "overrides",
    [
        # Bare string
        ["foobar"],
        # Unquoted string
        ["key=foobar"],
        # Unbalanced quote
        ["key='foobar"],
        # Unmatched brackets
        ['key=[1, "two",'],
        # Unmatches parentheses
        ['key={a=1, b="two"'],
        # Valid value followed by invalid
        ["good=42", "key=foobar"],
    ],
)
def test_invalid_overrides(overrides):
    with pytest.raises(
        BriefcaseCommandError,
        match=r"Unable to parse configuration override ",
    ):
        parse_config_overrides(overrides)
