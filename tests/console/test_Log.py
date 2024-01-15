import datetime
import logging
from io import TextIOBase
from unittest.mock import MagicMock, PropertyMock, call

import pytest
from rich.traceback import Trace

import briefcase
from briefcase.commands.dev import DevCommand
from briefcase.console import Console, Log, LogLevel, RichLoggingHandler
from briefcase.exceptions import BriefcaseError

TRACEBACK_HEADER = "Traceback (most recent call last)"
EXTRA_HEADER = "Extra information:"


@pytest.fixture
def mock_now(monkeypatch):
    """Monkeypatch the ``datetime.now`` inside ``briefcase.console``.

    When this fixture is used, the log filename for the test will be
    ``briefcase.2022_06_25-16_12_29.dev.log``, assuming the command is a DevCommand.
    """
    now = datetime.datetime(2022, 6, 25, 16, 12, 29)
    datetime_mock = MagicMock(wraps=datetime.datetime)
    datetime_mock.now.return_value = now
    monkeypatch.setattr(briefcase.console, "datetime", datetime_mock)
    return now


@pytest.fixture
def command(mock_now, tmp_path) -> DevCommand:
    """Provides a mocked DevCommand."""
    command = MagicMock(spec_set=DevCommand(Log(), Console()))
    command.base_path = tmp_path
    command.command = "dev"
    command.tools.os.environ = {}
    return command


@pytest.fixture
def logging_logger() -> logging.Logger:
    logging_logger = logging.getLogger("test_pkg")
    yield logging_logger
    # reset handlers since they are persistent
    logging_logger.handlers.clear()


@pytest.mark.parametrize(
    "verbosity, verbose_enabled, debug_enabled, deep_debug_enabled",
    [
        (-1, False, False, False),
        (0, False, False, False),
        (LogLevel.INFO, False, False, False),
        (1, True, False, False),
        (LogLevel.VERBOSE, True, False, False),
        (2, True, True, False),
        (LogLevel.DEBUG, True, True, False),
        (3, True, True, True),
        (LogLevel.DEEP_DEBUG, True, True, True),
        (4, True, True, True),
        (5, True, True, True),
    ],
)
def test_log_level(verbosity, verbose_enabled, debug_enabled, deep_debug_enabled):
    """Logging level is correct."""
    assert Log(verbosity=verbosity).is_verbose is verbose_enabled
    assert Log(verbosity=verbosity).is_debug is debug_enabled
    assert Log(verbosity=verbosity).is_deep_debug is deep_debug_enabled


def test_info_logging(capsys):
    """The info level logging only includes info logs."""
    logger = Log()

    logger.info("info")
    logger.verbose("verbose")
    logger.debug("debug")

    output = capsys.readouterr().out.splitlines()

    assert "info" in output
    assert "verbose" not in output
    assert "debug" not in output


def test_verbose_logging(capsys):
    """The verbose level logging includes info and verbose logs."""
    logger = Log(verbosity=LogLevel.VERBOSE)

    logger.info("info")
    logger.verbose("verbose")
    logger.debug("debug")

    output = capsys.readouterr().out.splitlines()

    assert "info" in output
    assert "verbose" in output
    assert "debug" not in output


def test_debug_logging(capsys):
    """The debug level logging includes info, verbose and debug logs."""
    logger = Log(verbosity=LogLevel.DEBUG)

    logger.info("info")
    logger.verbose("verbose")
    logger.debug("debug")

    output = capsys.readouterr().out.splitlines()

    assert "info" in output
    assert "verbose" in output
    assert "debug" in output


def test_capture_stacktrace():
    """capture_stacktrace sets Log.stacktrace."""
    logger = Log()
    assert logger.skip_log is False

    try:
        1 / 0
    except ZeroDivisionError:
        logger.capture_stacktrace()

    assert len(logger.stacktraces) == 1
    assert logger.stacktraces[0][0] == "Main thread"
    assert isinstance(logger.stacktraces[0][1], Trace)
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

    assert len(logger.stacktraces) == 1
    assert logger.stacktraces[0][0] == "Main thread"
    assert isinstance(logger.stacktraces[0][1], Trace)
    assert logger.skip_log is skip_logfile


def test_save_log_to_file_do_not_log(command):
    """Nothing is done to save log if no command or --log wasn't passed."""
    logger = Log()
    logger.save_log_to_file(command=None)

    logger.save_log = False
    logger.save_log_to_file(command=command)
    command.input.wait_bar.assert_not_called()

    # There were no stack traces captured
    assert len(logger.stacktraces) == 0


def test_save_log_to_file_no_exception(mock_now, command, tmp_path):
    """Log file contains everything printed to log; env vars are sanitized; no
    stacktrace if one is not captured."""
    command.tools.os.environ = {
        "GITHUB_KEY": "super-secret-key",
        "ANDROID_HOME": "/androidsdk",
    }

    logger = Log(verbosity=LogLevel.DEBUG)
    logger.save_log = True
    logger.debug("this is debug output")
    logger.info("this is info output")
    logger.warning("this is warning output")
    logger.error("this is error output")
    logger.print("this is print output")
    logger.print.to_log("this is log output")
    logger.print.to_log(f"{chr(7)}this is sanitized log output: \u001b[31mred")
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

    log_filepath = tmp_path / "logs/briefcase.2022_06_25-16_12_29.dev.log"

    assert log_filepath.exists()
    with open(log_filepath, encoding="utf-8") as log:
        log_contents = log.read()

    assert log_contents.startswith("Date/Time:       2022-06-25 16:12:29")
    assert "this is debug output" in log_contents
    assert "this is info output" in log_contents
    assert "this is [bold]info output with markup[/bold]" in log_contents
    assert "this is info output with escaped markup" in log_contents
    assert "this is warning output" in log_contents
    assert "this is error output" in log_contents
    assert "this is print output" in log_contents
    assert "this is log output" in log_contents
    assert "this is sanitized log output: red" in log_contents
    assert "this is console output" not in log_contents
    # Environment variables are in the output
    assert "ANDROID_HOME=/androidsdk" in log_contents
    assert "GITHUB_KEY=********************" in log_contents
    assert "GITHUB_KEY=super-secret-key" not in log_contents
    # Environment variables are sorted
    assert log_contents.index("ANDROID_HOME") < log_contents.index("GITHUB_KEY")

    assert TRACEBACK_HEADER not in log_contents
    assert EXTRA_HEADER not in log_contents


def test_save_log_to_file_with_exception(mock_now, command, tmp_path):
    """Log file contains exception stacktrace when one is captured."""
    logger = Log()
    logger.save_log = True
    try:
        1 / 0
    except ZeroDivisionError:
        logger.capture_stacktrace()
    logger.save_log_to_file(command=command)

    log_filepath = tmp_path / "logs/briefcase.2022_06_25-16_12_29.dev.log"

    assert log_filepath.exists()
    with open(log_filepath, encoding="utf-8") as log:
        log_contents = log.read()

    assert len(logger.stacktraces) == 1
    assert log_contents.startswith("Date/Time:       2022-06-25 16:12:29")
    assert TRACEBACK_HEADER in log_contents
    assert log_contents.splitlines()[-1].startswith("ZeroDivisionError")


def test_save_log_to_file_with_multiple_exceptions(mock_now, command, tmp_path):
    """Log file contains exception stacktrace when more than one is captured."""
    logger = Log()
    logger.save_log = True
    for i in range(1, 5):
        try:
            1 / 0
        except ZeroDivisionError:
            logger.capture_stacktrace(f"Thread {i}")

    logger.save_log_to_file(command=command)

    log_filepath = tmp_path / "logs/briefcase.2022_06_25-16_12_29.dev.log"

    assert log_filepath.exists()
    with open(log_filepath, encoding="utf-8") as log:
        log_contents = log.read()

    assert len(logger.stacktraces) == 4
    assert log_contents.startswith("Date/Time:       2022-06-25 16:12:29")
    assert TRACEBACK_HEADER in log_contents
    for i in range(1, 5):
        assert f"\nThread {i} traceback:\n" in log_contents
    assert log_contents.splitlines()[-1].startswith("ZeroDivisionError")


def test_save_log_to_file_extra(mock_now, command, tmp_path):
    """Log file extras are called when the log is written."""
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
    log_filepath = tmp_path / "logs/briefcase.2022_06_25-16_12_29.dev.log"
    with open(log_filepath, encoding="utf-8") as log:
        log_contents = log.read()

    assert EXTRA_HEADER in log_contents
    assert "Log extra 1" in log_contents
    assert TRACEBACK_HEADER in log_contents
    assert "ValueError: Log extra 2" in log_contents
    assert "Log extra 3" in log_contents


def test_save_log_to_file_extra_interrupted(mock_now, command, tmp_path):
    """Log file extras can be interrupted by Ctrl-C."""
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
    log_filepath = tmp_path / "logs/briefcase.2022_06_25-16_12_29.dev.log"
    assert log_filepath.stat().st_size == 0


def test_save_log_to_file_fail_to_make_logs_dir(
    mock_now,
    command,
    capsys,
    monkeypatch,
    tmp_path,
):
    """User is informed when the ``logs`` directory cannot be created."""
    # Mock the command's base path such that it:
    mock_base_path = MagicMock(wraps=tmp_path)
    command.base_path = mock_base_path
    #  - returns a mocked filepath for the log file
    mock_base_path.__str__.return_value = "/asdf/log_filepath"
    #  - returns itself when the "logs" directory and log filename are appended
    #    to create the full filepath to the log file
    mock_base_path.__truediv__.return_value = mock_base_path
    #  - returns itself when ``Log`` requests the ``parent`` for the log filepath
    type(mock_base_path).parent = PropertyMock(return_value=mock_base_path)
    #  - raises for the call to ``mkdir`` to create the ``logs`` directory
    mock_base_path.mkdir.side_effect = OSError("directory creation denied")

    logger = Log()
    logger.save_log = True

    logger.print("a line of output")
    logger.save_log_to_file(command=command)

    assert capsys.readouterr().out == "\n".join(
        [
            "a line of output",
            "",
            "Failed to save log to /asdf/log_filepath: directory creation denied",
            "",
            "",
        ]
    )


def test_save_log_to_file_fail_to_write_file(
    mock_now,
    command,
    capsys,
    monkeypatch,
    tmp_path,
):
    """User is informed when the log file cannot be written."""
    # Mock opening a file that raises PermissionError on write
    mock_open = MagicMock(spec_set=open)
    monkeypatch.setattr("builtins.open", mock_open)
    mock_log_file = MagicMock(spec_set=TextIOBase)
    mock_open.return_value.__enter__.return_value = mock_log_file
    mock_log_file.write.side_effect = OSError("file write denied")

    logger = Log()
    logger.save_log = True

    logger.print("a line of output")
    logger.save_log_to_file(command=command)

    log_filepath = tmp_path / "logs/briefcase.2022_06_25-16_12_29.dev.log"
    assert capsys.readouterr().out == "\n".join(
        [
            "a line of output",
            "",
            f"Failed to save log to {log_filepath}: file write denied",
            "",
            "",
        ]
    )


def test_log_with_context(capsys):
    """Log file can be given a persistent context."""
    logger = Log(verbosity=LogLevel.DEBUG)
    logger.save_log = False

    logger.info("this is info output")
    with logger.context("Deep"):
        logger.info("this is deep context")
        logger.info("prefixed deep context", prefix="prefix")
        logger.info()
        logger.debug("this is deep debug")
        with logger.context("Really Deep"):
            logger.info("this is really deep context")
            logger.info("prefixed really deep context", prefix="prefix2")
            logger.info()
            logger.debug("this is really deep debug")
        logger.info("Pop back to deep")
    logger.info("Pop back to normal")

    assert capsys.readouterr().out == "\n".join(
        [
            "this is info output",
            "",
            "Entering Deep context...",
            "Deep| --------------------------------------------------------------------",
            "Deep| this is deep context",
            "Deep| ",
            "Deep| [prefix] prefixed deep context",
            "Deep| ",
            "Deep| this is deep debug",
            "Deep| ",
            "Deep| Entering Really Deep context...",
            "Really Deep| -------------------------------------------------------------",
            "Really Deep| this is really deep context",
            "Really Deep| ",
            "Really Deep| [prefix2] prefixed really deep context",
            "Really Deep| ",
            "Really Deep| this is really deep debug",
            "Really Deep| -------------------------------------------------------------",
            "Deep| Leaving Really Deep context.",
            "Deep| ",
            "Deep| Pop back to deep",
            "Deep| --------------------------------------------------------------------",
            "Leaving Deep context.",
            "",
            "Pop back to normal",
            "",
        ]
    )


def test_log_error_with_context(capsys):
    """If an exception is raised in a logging context, the context is cleared."""
    logger = Log(verbosity=LogLevel.DEBUG)
    logger.save_log = False

    logger.info("this is info output")
    try:
        with logger.context("Deep"):
            logger.info("this is deep context")
            raise ValueError()
    except ValueError:
        logger.info("this is cleanup")

    assert capsys.readouterr().out == "\n".join(
        [
            "this is info output",
            "",
            "Entering Deep context...",
            "Deep| --------------------------------------------------------------------",
            "Deep| this is deep context",
            "Deep| --------------------------------------------------------------------",
            "Leaving Deep context.",
            "",
            "this is cleanup",
            "",
        ]
    )


@pytest.mark.parametrize(
    "logging_level, handler_expected",
    [
        (LogLevel.DEEP_DEBUG, True),
        (LogLevel.DEBUG, False),
        (LogLevel.VERBOSE, False),
        (LogLevel.INFO, False),
    ],
)
def test_stdlib_logging_config(logging_level, handler_expected, logging_logger):
    """A logging handler is only added for DEEP_DEBUG mode."""
    logger = Log(verbosity=logging_level)

    logger.configure_stdlib_logging("test_pkg")

    assert handler_expected is any(
        isinstance(h, RichLoggingHandler) for h in logging_logger.handlers
    )


def test_stdlib_logging_only_one(logging_logger):
    """Only one logging handler is ever created for a package."""
    logger = Log(verbosity=LogLevel.DEEP_DEBUG)

    logger.configure_stdlib_logging("test_pkg")
    logger.configure_stdlib_logging("test_pkg")
    logger.configure_stdlib_logging("test_pkg")

    assert len(logging_logger.handlers) == 1


def test_stdlib_logging_handler_writes_to_debug(logging_logger):
    """The logging handler writes to the console through Log()."""
    logger = Log(verbosity=LogLevel.DEEP_DEBUG)
    logger.debug = MagicMock(wraps=logger.debug)

    logger.configure_stdlib_logging("test_pkg")

    logging_logger.debug("This is debug output")
    logging_logger.info("This is info output")

    assert logger.debug.mock_calls == [
        call("DEBUG test_pkg: This is debug output\n"),
        call("INFO test_pkg: This is info output\n"),
    ]
