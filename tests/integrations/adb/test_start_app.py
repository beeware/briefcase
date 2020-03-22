from unittest.mock import MagicMock

import pytest

from briefcase.exceptions import BriefcaseCommandError
from briefcase.integrations.adb import ADB


def test_start_app_launches_app(tmp_path, capsys):
    "Invoking `start_app()` calls `run()` with the appropriate parameters."
    # Mock out the run command on an adb instance
    adb = ADB(tmp_path, "exampleDevice")
    adb.command = MagicMock(return_value=b"example normal adb output")

    # Invoke start_app
    adb.start_app("com.example.sample.package", "com.example.sample.activity")

    # Validate call parameters.
    adb.command.assert_called_once_with(
        "shell",
        "am",
        "start",
        "com.example.sample.package/com.example.sample.activity",
        "-a",
        "android.intent.action.MAIN",
        "-c",
        "android.intent.category.LAUNCHER",
    )

    # Validate that the normal output of the command was not printed (since there
    # was no error).
    assert "normal adb output" not in capsys.readouterr()


def test_missing_activity(tmp_path):
    "If the activity doesn't exist, the error is caught."
    # Use real `adb` output from launching an activity that does not exist.
    # Mock out the run command on an adb instance
    adb = ADB(tmp_path, "exampleDevice")
    adb.command = MagicMock(return_value=b"""\
Starting: Intent { act=android.intent.action.MAIN cat=[android.intent.category.\
LAUNCHER] cmp=com.example.sample.package/.MainActivity }
Error type 3
Error: Activity class {com.example.sample.package/com.example.sample.package.\
MainActivity} does not exist.
""")

    with pytest.raises(BriefcaseCommandError) as exc_info:
        adb.start_app("com.example.sample.package", "com.example.sample.activity")

    assert "Activity class not found" in str(exc_info.value)
