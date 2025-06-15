import json
import shlex
from subprocess import CalledProcessError
from unittest.mock import MagicMock

import pytest

from briefcase.exceptions import BriefcaseCommandError, InvalidDeviceError


@pytest.mark.parametrize(
    "passthrough",
    [
        [],
        [""],
        ['"'],
        ["\\"],
        ["one"],
        ["one two"],
        ["one\ntwo"],
        ["one,two"],
        ["one", "two"],
        ["one", "two", "three"],
    ],
)
def test_start_app_launches_app(adb, capsys, passthrough):
    """Invoking `start_app()` calls `run()` with the appropriate parameters."""
    # Mock out the run command on an adb instance
    adb.run = MagicMock(return_value="example normal adb output")

    # Invoke start_app
    adb.start_app(
        "com.example.sample.package", "com.example.sample.activity", passthrough
    )

    # Validate call parameters.
    adb.run.assert_called_once_with(
        "shell",
        "am",
        "start",
        "-n",
        "com.example.sample.package/com.example.sample.activity",
        "-a",
        "android.intent.action.MAIN",
        "-c",
        "android.intent.category.LAUNCHER",
        "--es",
        "org.beeware.ARGV",
        shlex.quote(json.dumps(passthrough)),
    )

    # Validate that the normal output of the command was not printed (since there
    # was no error).
    assert "normal adb output" not in capsys.readouterr()


def test_missing_activity(adb):
    """If the activity doesn't exist, the error is caught."""
    # Use real `adb` output from launching an activity that does not exist.
    # Mock out the run command on an adb instance
    adb.run = MagicMock(
        return_value="""\
Starting: Intent { act=android.intent.action.MAIN cat=[android.intent.category.\
LAUNCHER] cmp=com.example.sample.package/.MainActivity }
Error type 3
Error: Activity class {com.example.sample.package/com.example.sample.package.\
MainActivity} does not exist.
"""
    )

    with pytest.raises(BriefcaseCommandError) as exc_info:
        adb.start_app("com.example.sample.package", "com.example.sample.activity", [])

    assert "Activity class not found" in str(exc_info.value)


def test_invalid_device(adb):
    """If the device doesn't exist, the error is caught."""
    # Use real `adb` output from launching an activity that does not exist.
    # Mock out the run command on an adb instance
    adb.run = MagicMock(side_effect=InvalidDeviceError("device", "exampleDevice"))

    with pytest.raises(InvalidDeviceError):
        adb.start_app("com.example.sample.package", "com.example.sample.activity", [])


def test_unable_to_start(adb):
    """If the adb calls for other reasons, the error is caught."""
    adb.run = MagicMock(side_effect=CalledProcessError(cmd=["adb"], returncode=1))

    with pytest.raises(
        BriefcaseCommandError,
        match=r"Unable to start com.example.sample.package/com.example.sample.activity on exampleDevice",
    ):
        adb.start_app("com.example.sample.package", "com.example.sample.activity", [])
