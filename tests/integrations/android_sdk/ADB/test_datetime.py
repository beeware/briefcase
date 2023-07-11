import subprocess
from datetime import datetime
from unittest.mock import Mock

import pytest

from briefcase.exceptions import BriefcaseCommandError
from briefcase.integrations.android_sdk import ADB


def test_datetime_success(mock_tools):
    """adb.datetime() returns `datetime` for device."""
    adb = ADB(mock_tools, "exampleDevice")
    adb.run = Mock(return_value="1689098555\n")

    expected_datetime = datetime(2023, 7, 11, 14, 2, 35)
    assert adb.datetime() == expected_datetime
    adb.run.assert_called_once_with("shell", "date", "+%s")


def test_datetime_failure_call(mock_tools):
    """adb.datetime() fails in subprocess call."""
    adb = ADB(mock_tools, "exampleDevice")
    adb.run = Mock(
        side_effect=subprocess.CalledProcessError(returncode=1, cmd="adb shell ...")
    )

    with pytest.raises(
        BriefcaseCommandError,
        match="Error obtaining device date/time.",
    ):
        adb.datetime()


def test_datetime_failure_bad_value(mock_tools):
    """adb.datetime() fails in output conversion."""
    adb = ADB(mock_tools, "exampleDevice")
    adb.run = Mock(return_value="this date is jan 1 1970")

    with pytest.raises(
        BriefcaseCommandError,
        match="Error obtaining device date/time.",
    ):
        adb.datetime()
