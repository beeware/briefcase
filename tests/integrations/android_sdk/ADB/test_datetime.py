import subprocess
from datetime import datetime
from unittest.mock import Mock

import pytest

from briefcase.exceptions import BriefcaseCommandError


@pytest.mark.parametrize(
    "device_output, expected_datetime",
    [
        ("2023-07-12 09:28:04", datetime(2023, 7, 12, 9, 28, 4)),
        ("2023-07-12 09:28:04\n", datetime(2023, 7, 12, 9, 28, 4)),
        ("2023-7-12 9:28:04", datetime(2023, 7, 12, 9, 28, 4)),
        ("2023-12-2 14:28:04", datetime(2023, 12, 2, 14, 28, 4)),
    ],
)
def test_datetime_success(adb, device_output, expected_datetime):
    """adb.datetime() returns `datetime` for device."""
    adb.run = Mock(return_value=device_output)

    assert adb.datetime() == expected_datetime
    adb.run.assert_called_once_with("shell", "date", "+'%Y-%m-%d %H:%M:%S'")


def test_datetime_failure_call(adb):
    """adb.datetime() fails in subprocess call."""
    adb.run = Mock(
        side_effect=subprocess.CalledProcessError(returncode=1, cmd="adb shell ...")
    )

    with pytest.raises(
        BriefcaseCommandError,
        match="Error obtaining device date/time.",
    ):
        adb.datetime()


def test_datetime_failure_bad_value(adb):
    """adb.datetime() fails in output conversion."""
    adb.run = Mock(return_value="the date is jan 1 1970")

    with pytest.raises(
        BriefcaseCommandError,
        match="Error obtaining device date/time.",
    ):
        adb.datetime()
