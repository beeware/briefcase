from unittest.mock import MagicMock

import pytest

from briefcase.integrations.cookiecutter import GradleEscape


@pytest.mark.parametrize(
    "value, expected",
    [
        ("Hello World", "Hello World"),
        ("Hello ' World", "Hello \\' World"),
        ("Hello \\ World", "Hello \\\\ World"),
    ],
)
def test_escape_gradle(value, expected):
    env = MagicMock()
    env.filters = {}
    GradleEscape(env)
    assert env.filters["escape_gradle"](value) == expected


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
    GradleEscape(env)
    assert env.filters["escape_non_ascii"](value) == expected
