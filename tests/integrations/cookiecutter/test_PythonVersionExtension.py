from unittest.mock import MagicMock

import pytest

from briefcase.integrations.cookiecutter import PythonVersionExtension


@pytest.mark.parametrize(
    "value, expected",
    [
        # Single digit minor
        ("3.8.4.dev5", "3.8"),
        ("3.8.4a1", "3.8"),
        ("3.8.4b2", "3.8"),
        ("3.8.4rc3", "3.8"),
        ("3.8.4.post6", "3.8"),
        # Two digit minor
        ("3.11.4.dev5", "3.11"),
        ("3.11.4a1", "3.11"),
        ("3.11.4b2", "3.11"),
        ("3.11.4rc3", "3.11"),
        ("3.11.4.post6", "3.11"),
    ],
)
def test_py_tag(value, expected):
    env = MagicMock()
    env.filters = {}
    PythonVersionExtension(env)
    assert env.filters["py_tag"](value) == expected


@pytest.mark.parametrize(
    "value, expected",
    [
        # Single digit minor
        ("3.8.4.dev5", "38"),
        ("3.8.4a1", "38"),
        ("3.8.4b2", "38"),
        ("3.8.4rc3", "38"),
        ("3.8.4.post6", "38"),
        # Two digit minor
        ("3.11.4.dev5", "311"),
        ("3.11.4a1", "311"),
        ("3.11.4b2", "311"),
        ("3.11.4rc3", "311"),
        ("3.11.4.post6", "311"),
    ],
)
def test_py_libtag(value, expected):
    env = MagicMock()
    env.filters = {}
    PythonVersionExtension(env)
    assert env.filters["py_libtag"](value) == expected
