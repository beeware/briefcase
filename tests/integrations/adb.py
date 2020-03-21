from pathlib import Path
from subprocess import CalledProcessError
from unittest.mock import MagicMock

import pytest

from briefcase.exceptions import BriefcaseCommandError
from briefcase.integrations.adb import (
    force_stop_app,
    install_apk,
    run_adb,
    start_app
)


def test_run_adb_runs_adb(tmp_path):
    """Validate that `run_adb()` calls adb with the expected parameters."""
    mock_subprocess = MagicMock()
    run_adb(tmp_path, "exampleDevice", ["example", "command"], mock_subprocess)
    mock_subprocess.check_output.assert_called_once_with(
        [
            str(tmp_path / "platform-tools" / "adb"),
            "-s",
            "exampleDevice",
            "example",
            "command",
        ],
        stderr=mock_subprocess.STDOUT,
    )


@pytest.mark.parametrize(
    "name,exception_text",
    [
        # When the device is not found, look for a command the user can run to get a
        # list of valid devices.
        ("device-not-found", "adb devices -l"),
        # Validate that when an arbitrary adb errors, we print the full adb output.
        # This adb output comes from asking it to run a nonexistent adb command.
        ("arbitrary-adb-error-unknown-command", "unknown command"),
    ],
)
def test_run_adb_handles_errors(tmp_path, name, exception_text):
    "Validate that `run_adb()` prints appropriate error text."
    # Set up a mock subprocess module with sample data loaded, then run `run_adb()`.
    mock_sub = MagicMock()
    adb_samples = Path(__file__).parent / "adb_samples"
    with (adb_samples / (name + ".txt")).open("rb") as adb_output_file:
        with (adb_samples / (name + ".returncode")).open() as returncode_file:
            mock_sub.check_output.side_effect = CalledProcessError(
                returncode=int(returncode_file.read().strip()),
                cmd=["ignored"],
                output=adb_output_file.read(),
            )
    with pytest.raises(BriefcaseCommandError) as exc_info:
        run_adb(tmp_path, "exampleDevice", ["example", "command"], mock_sub)
    # Look for expected exception text.
    assert exception_text in str(exc_info)


@pytest.fixture
def mock_run_adb():
    """Create a mock `run_adb()` function.

    This allows other tests to make assertions about how `run_adb()` was called."""
    return MagicMock(return_value=b"example normal adb output")


def test_install_apk(mock_run_adb, capsys, tmp_path):
    "Validate that `install_apk()` calls `run_adb` with the appropriate parameters."
    install_apk(
        tmp_path / "example_sdk_path",
        "exampleDevice",
        "example.apk",
        run_adb=mock_run_adb,
    )
    # Validate call parameters.
    mock_run_adb.assert_called_once_with(
        tmp_path / "example_sdk_path", "exampleDevice", ["install", "example.apk"]
    )
    # Validate that the normal output of the command was not printed (since there
    # was no error).
    assert "normal adb output" not in capsys.readouterr()


def test_force_stop_app(mock_run_adb, capsys, tmp_path):
    "Validate that `force_stop_app()` calls `run_adb` with the appropriate parameters."
    force_stop_app(
        tmp_path / "example_sdk_path",
        "exampleDevice",
        "com.example.sample.package",
        run_adb=mock_run_adb,
    )
    # Validate call parameters.
    mock_run_adb.assert_called_once_with(
        tmp_path / "example_sdk_path",
        "exampleDevice",
        ["shell", "am", "force-stop", "com.example.sample.package"],
    )
    # Validate that the normal output of the command was not printed (since there
    # was no error).
    assert "normal adb output" not in capsys.readouterr()


def test_start_app_launches_app(mock_run_adb, capsys, tmp_path):
    "Validate that `start_app()` passes the right parameters to `run_adb()`."
    start_app(
        tmp_path / "example_sdk_path",
        "exampleDevice",
        "com.example.sample.package",
        "com.example.sample.activity",
        run_adb=mock_run_adb,
    )
    # Validate call parameters.
    mock_run_adb.assert_called_once_with(
        tmp_path / "example_sdk_path",
        "exampleDevice",
        [
            "shell",
            "am",
            "start",
            "com.example.sample.package/com.example.sample.activity",
            "-a",
            "android.intent.action.MAIN",
            "-c",
            "android.intent.category.LAUNCHER",
        ],
    )
    # Validate that the normal output of the command was not printed (since there
    # was no error).
    assert "normal adb output" not in capsys.readouterr()


def test_start_app_detects_missing_activity(mock_run_adb, tmp_path):
    """Validate that `start_app()` examines `adb` output to detect if the Android
    activity it tried to start does not exist."""
    # Use real `adb` output from launching an activity that does not exist.
    adb_output = b"""\
Starting: Intent { act=android.intent.action.MAIN cat=[android.intent.category.\
LAUNCHER] cmp=com.example.sample.package/.MainActivity }
Error type 3
Error: Activity class {com.example.sample.package/com.example.sample.package.\
MainActivity} does not exist.
"""
    mock_run_adb.return_value = adb_output
    with pytest.raises(BriefcaseCommandError) as exc_info:
        start_app(
            tmp_path / "example_sdk_path",
            "exampleDevice",
            "com.example.sample.package",
            "com.example.sample.activity",
            run_adb=mock_run_adb,
        )
    assert "Activity class not found" in str(exc_info)
