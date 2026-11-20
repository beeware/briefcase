from unittest.mock import MagicMock

import pytest

from briefcase.integrations.cookiecutter import TextExtension


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        # No items
        ([], ""),
        # A single item is used as-is
        (["Alice"], "Alice"),
        # Two items are joined with "and"
        (["Alice", "Bob"], "Alice and Bob"),
        # Three or more items are comma separated, with "and" before the last
        (["Alice", "Bob", "Carol"], "Alice, Bob and Carol"),
        (["Alice", "Bob", "Carol", "Dave"], "Alice, Bob, Carol and Dave"),
        # Any iterable can be joined
        (("Alice", "Bob"), "Alice and Bob"),
    ],
)
def test_lexical_join(value, expected):
    env = MagicMock()
    env.filters = {}
    TextExtension(env)
    assert env.filters["lexical_join"](value) == expected
