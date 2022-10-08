import datetime
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from rich.traceback import Trace

import briefcase
from briefcase.console import Log
from briefcase.exceptions import BriefcaseError

TRACEBACK_HEADER = "Traceback (most recent call last)"
EXTRA_HEADER = "Extra information:"


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
    assert logger.skip_log is False

    try:
        1 / 0
    except ZeroDivisionError:
        logger.capture_stacktrace()

    assert isinstance(logger.stacktrace, Trace)
    assert logger.skip_log is False


@pytest.mark.parametrize("skip_logfile", [True, False])
def test_capture_stacktrace_for_briefcaseerror(skip_logfile):
    """skip_log is updated for BriefcaseError exceptions."""
    logger = Log()
    assert logger.skip_log is False

    try:
        raise BriefcaseError(error_code=542, skip_logfile=skip_logfile)
    except BriefcaseError:
        logger.capture_stacktrace()

    assert isinstance(logger.stacktrace, Trace)
    assert logger.skip_log is skip_logfile


def test_save_log_to_file_do_not_log():
    """Nothing is done to save log if no command or --log wasn't passed."""
    logger = Log()
    logger.save_log_to_file(command=None)

    command = MagicMock()
    logger.save_log = False
    logger.save_log_to_file(command=command)
    command.input.wait_bar.assert_not_called()


def test_save_log_to_file_no_exception(tmp_path, now):
    """Log file contains everything printed to log; env vars are sanitized; no
    stacktrace if one is not captured."""
    command = MagicMock()
    command.base_path = Path(tmp_path)
    command.command = "dev"
    command.tools.os.environ = {
        "GITHUB_KEY": "super-secret-key",
        "ANDROID_SDK_ROOT": "/androidsdk",
    }

    logger = Log(verbosity=2)
    logger.save_log = True
    logger.debug("this is debug output")
    logger.info("this is info output")
    logger.warning("this is warning output")
    logger.error("this is error output")
    logger.print("this is print output")
    logger.print.to_log("this is log output")
    logger.print.to_console("this is console output")

    logger.info("this is [bold]info output with markup[/bold]")
    logger.info(
        "this is [bold]info output with markup and a prefix[/bold]", prefix="wibble"
    )
    logger.info("this is [bold]info output with escaped markup[/bold]", markup=True)
    logger.info(
        "this is [bold]info output with escaped markup and a prefix[/bold]",
        prefix="wibble",
        markup=True,
    )

    logger.save_log_to_file(command=command)

    log_filepath = tmp_path / logger.LOG_DIR / "briefcase.2022_06_25-16_12_29.dev.log"

    assert log_filepath.exists()
    with open(log_filepath, encoding="utf-8") as log:
        log_contents = log.read()

    assert log_contents.startswith("Date/Time:       2022-06-25 16:12:29")
    assert f"{Log.DEBUG_PREFACE}this is debug output" in log_contents
    assert "this is info output" in log_contents
    assert "this is [bold]info output with markup[/bold]" in log_contents
    assert "this is info output with escaped markup" in log_contents
    assert "this is warning output" in log_contents
    assert "this is error output" in log_contents
    assert "this is print output" in log_contents
    assert "this is log output" in log_contents
    assert "this is console output" not in log_contents
    # Environment variables are in the output
    assert "ANDROID_SDK_ROOT=/androidsdk" in log_contents
    assert "GITHUB_KEY=********************" in log_contents
    assert "GITHUB_KEY=super-secret-key" not in log_contents
    # Environment variables are sorted
    assert log_contents.index("ANDROID_SDK_ROOT") < log_contents.index("GITHUB_KEY")

    assert TRACEBACK_HEADER not in log_contents
    assert EXTRA_HEADER not in log_contents


def test_save_log_to_file_with_exception(tmp_path, now):
    """Log file contains exception stacktrace when one is captured."""
    command = MagicMock()
    command.base_path = Path(tmp_path)
    command.command = "dev"
    command.tools.os.environ = {}

    logger = Log()
    logger.save_log = True
    try:
        1 / 0
    except ZeroDivisionError:
        logger.capture_stacktrace()
    logger.save_log_to_file(command=command)

    log_filepath = tmp_path / logger.LOG_DIR / "briefcase.2022_06_25-16_12_29.dev.log"

    log_filepath.exists()
    with open(log_filepath, encoding="utf-8") as log:
        log_contents = log.read()

    assert log_contents.startswith("Date/Time:       2022-06-25 16:12:29")
    assert TRACEBACK_HEADER in log_contents
    assert log_contents.splitlines()[-1].startswith("ZeroDivisionError")


def test_save_log_to_file_extra(tmp_path, now):
    """Log file extras are called when the log is written."""
    command = MagicMock()
    command.base_path = Path(tmp_path)
    command.command = "dev"

    logger = Log()
    logger.save_log = True

    def extra1():
        logger.debug("Log extra 1")

    def extra2():
        raise ValueError("Log extra 2")

    def extra3():
        logger.debug("Log extra 3")

    for extra in [extra1, extra2, extra3]:
        logger.add_log_file_extra(extra)
    logger.save_log_to_file(command=command)
    log_filepath = tmp_path / logger.LOG_DIR / "briefcase.2022_06_25-16_12_29.dev.log"
    with open(log_filepath, encoding="utf-8") as log:
        log_contents = log.read()

    assert EXTRA_HEADER in log_contents
    assert "Log extra 1" in log_contents
    assert TRACEBACK_HEADER in log_contents
    assert "ValueError: Log extra 2" in log_contents
    assert "Log extra 3" in log_contents


def test_save_log_to_file_extra_interrupted(tmp_path, now):
    """Log file extras can be interrupted by Ctrl-C."""
    command = MagicMock()
    command.base_path = Path(tmp_path)
    command.command = "dev"

    logger = Log()
    logger.save_log = True

    def extra1():
        raise KeyboardInterrupt()

    extra2 = MagicMock()
    for extra in [extra1, extra2]:
        logger.add_log_file_extra(extra)
    with pytest.raises(KeyboardInterrupt):
        logger.save_log_to_file(command=command)
    extra2.assert_not_called()
    log_filepath = tmp_path / logger.LOG_DIR / "briefcase.2022_06_25-16_12_29.dev.log"
    assert log_filepath.stat().st_size == 0


def test_save_log_to_file_fail_to_write_file(capsys):
    """User is informed when the log file cannot be written."""
    command = MagicMock()
    command.base_path = Path("/a-path-that-will-cause-an-OSError...")
    command.command = "dev"
    command.tools.os.environ = {}

    logger = Log()
    logger.save_log = True

    logger.print("a line of output")
    logger.save_log_to_file(command=command)

    last_line_of_output = capsys.readouterr().out.strip().splitlines()[-1]
    assert last_line_of_output.startswith("Failed to save log to ")
