import pytest

from briefcase.commands.base import parse_config_overrides
from briefcase.exceptions import BriefcaseConfigError


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
    "overrides, message",
    [
        # Bare string
        (["foobar"], r"Unable to parse configuration override "),
        # Unquoted string
        (["key=foobar"], r"Unable to parse configuration override "),
        # Unbalanced quote
        (["key='foobar"], r"Unable to parse configuration override "),
        # Unmatched brackets
        (['key=[1, "two",'], r"Unable to parse configuration override "),
        # Unmatches parentheses
        (['key={a=1, b="two"'], r"Unable to parse configuration override "),
        # Valid value followed by invalid
        (["good=42", "key=foobar"], r"Unable to parse configuration override "),
        # Space in the key.
        (["spacy key=42"], r"Unable to parse configuration override "),
        # Multi-level key. This is legal TOML, but difficult to merge.
        (["multi.level.key=42"], r"Can't override multi-level configuration keys\."),
        # Key that can't be overridden
        (["app_name='foobar'"], r"The app name cannot be overridden\."),
    ],
)
def test_invalid_overrides(overrides, message):
    with pytest.raises(BriefcaseConfigError, match=message):
        parse_config_overrides(overrides)
