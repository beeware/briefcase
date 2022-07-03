import datetime
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from rich.traceback import Trace

import briefcase
from briefcase.console import Log


@pytest.fixture
def now(monkeypatch):
    """monkeypatch the datetime.now inside of briefcase.console."""
    now = datetime.datetime(2022, 6, 25, 16, 12, 29)
    datetime_mock = MagicMock(wraps=datetime.datetime)
    datetime_mock.now.return_value = now
    monkeypatch.setattr(briefcase.console, "datetime", datetime_mock)
    return now


def test_capture_stacktrace():
    """capture_stacktrace sets Log.stacktrace."""
    logger = Log()
    try:
        1 / 0
    except ZeroDivisionError:
        logger.capture_stacktrace()
    assert isinstance(logger.stacktrace, Trace)


def test_save_log_to_file_do_not_log():
    """Nothing is done to save log if no command or --log wasn't passed."""
    logger = Log()
    logger.save_log_to_file(command=None)

    command = MagicMock()
    command.save_log = False
    logger.save_log_to_file(command=command)
    command.input.wait_bar.assert_not_called()


def test_save_log_to_file_no_exception(tmp_path, now):
    """Log file contains everything printed to log; env vars are sanitized; no
    stacktrace if one is not captured."""
    command = MagicMock()
    command.base_path = Path(tmp_path)
    command.command = "dev"
    command.save_log = True
    command.os.environ = {
        "GITHUB_KEY": "super-secret-key",
        "ANDROID_SDK_ROOT": "/androidsdk",
    }

    logger = Log(verbosity=2)
    logger.debug("this is debug output")
    logger.info("this is info output")
    logger.warning("this is warning output")
    logger.error("this is error output")
    logger.print("this is print output")
    logger.print.to_log("this is log output")
    logger.print.to_console("this is console output")

    logger.save_log_to_file(command=command)

    log_filepath = tmp_path / "briefcase.2022_06_25-16_12_29.dev.log"

    assert log_filepath.exists()
    log_contents = open(log_filepath, encoding="utf-8").read()

    assert log_contents.startswith("Date/Time:       2022-06-25 16:12:29")
    assert f"{Log.DEBUG_PREFACE}this is debug output" in log_contents
    assert "this is info output" in log_contents
    assert "this is warning output" in log_contents
    assert "this is error output" in log_contents
    assert "this is print output" in log_contents
    assert "this is log output" in log_contents
    assert "this is console output" not in log_contents
    # Environment variables are in the output
    assert "ANDROID_SDK_ROOT=/androidsdk" in log_contents
    assert "GITHUB_KEY=********************" in log_contents
    # Environment variables are sorted
    assert log_contents.index("ANDROID_SDK_ROOT") < log_contents.index("GITHUB_KEY")
    assert "Traceback (most recent call last)" not in log_contents


def test_save_log_to_file_with_exception(tmp_path, now):
    """Log file contains exception stacktrace when one is captured."""
    command = MagicMock()
    command.base_path = Path(tmp_path)
    command.command = "dev"
    command.save_log = True
    command.os.environ = {}

    logger = Log()
    try:
        1 / 0
    except ZeroDivisionError:
        logger.capture_stacktrace()
    logger.save_log_to_file(command=command)

    log_filepath = tmp_path / "briefcase.2022_06_25-16_12_29.dev.log"

    log_filepath.exists()
    log_contents = open(log_filepath, encoding="utf-8").read()

    assert log_contents.startswith("Date/Time:       2022-06-25 16:12:29")
    assert "Traceback (most recent call last)" in log_contents
    assert log_contents.splitlines()[-1].startswith("ZeroDivisionError")


def test_save_log_to_file_fail_to_write_file(capsys):
    """User is informed when the log file cannot be written."""
    command = MagicMock()
    command.base_path = Path("/a-path-that-will-cause-an-OSError...")
    command.command = "dev"
    command.save_log = True
    command.os.environ = {}

    logger = Log()
    logger.print("a line of output")
    logger.save_log_to_file(command=command)

    last_line_of_output = capsys.readouterr().out.strip().splitlines()[-1]
    assert last_line_of_output.startswith("Failed to save log to ")
