from unittest.mock import MagicMock

import pytest

from briefcase.integrations.cookiecutter import PListExtension


@pytest.mark.parametrize(
    "value, expected",
    [
        (True, "<true/>"),
        (False, "<false/>"),
        ("Hello world", "<string>Hello world</string>"),
    ],
)
def test_plist_value(value, expected):
    env = MagicMock()
    env.filters = {}
    PListExtension(env)
    assert env.filters["plist_value"](value) == expected
