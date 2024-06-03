from unittest.mock import MagicMock

import pytest

from briefcase.integrations.cookiecutter import UUIDExtension


@pytest.mark.parametrize(
    "value, expected",
    [
        ("example.com", "cfbff0d1-9375-5685-968c-48ce8b15ae17"),
        ("foobar.example.com", "941bbcd9-03e1-568a-a728-8434055bc338"),
    ],
)
def test_dns_uuid5_value(value, expected):
    env = MagicMock()
    env.filters = {}
    UUIDExtension(env)
    assert env.filters["dns_uuid5"](value) == expected
