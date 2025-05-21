import sys
from collections import namedtuple
from datetime import datetime
from unittest import mock

import pytest

import briefcase


def _create_version_info(major, minor, patch=0):
    Version = namedtuple("Version", "major minor patch")
    return Version(major, minor, patch)


@pytest.mark.parametrize(
    "minor_version, today, is_valid",
    [
        (8, datetime(2025, 10, 1), False),  # after EOL
        (9, datetime(2025, 10, 1), True),  # on EOL
        (9, datetime(2025, 10, 2), False),  # after EOL
        (10, datetime(2026, 9, 30), True),  # before EOL
        (10, datetime(2026, 10, 2), False),  # after EOL
        (14, datetime(2030, 9, 30), True),  # before EOL
        (14, datetime(2030, 10, 2), False),  # after EOL
    ],
)
def test_valid_python_version(
    minor_version, today, is_valid, base_command, monkeypatch
):
    """A warning is produced if the Python version is past its EOL"""

    version_info = _create_version_info(3, minor_version)
    sys_mock = mock.MagicMock(wraps=sys)
    sys_mock.version_info = version_info
    monkeypatch.setattr(briefcase.commands.base, "sys", sys_mock)

    datetime_mock = mock.MagicMock(wraps=datetime)
    datetime_mock.today.return_value = today
    monkeypatch.setattr(briefcase.commands.base, "datetime", datetime_mock)

    assert base_command.validate_python_version() is is_valid
