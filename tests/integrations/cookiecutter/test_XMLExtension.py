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
