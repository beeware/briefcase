import subprocess
from datetime import datetime
from unittest.mock import Mock

import pytest

from briefcase.exceptions import BriefcaseCommandError


def test_datetime_success(adb):
    """adb.datetime() returns `datetime` for device."""
    adb.run = Mock(return_value="1689098555\n")

    # Cannot hardcode the actual datetime of 1689098555 since
    # it is dependent on the timezone of the host system
    expected_datetime = datetime.fromtimestamp(1689098555)
    assert adb.datetime() == expected_datetime
    adb.run.assert_called_once_with("shell", "date", "+%s")


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
