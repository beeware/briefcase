import re

import pytest

from briefcase.console import Printer


@pytest.fixture
def printer():
    printer = Printer()
    # clear log; since Printer is a pseudo-singleton,
    # the log can contain existing entries.
    printer.export_log()
    return printer


def norm_sp(text: str, max_spaces: int = 100) -> str:
    """Normalize more than `max_spaces` spaces in text to `max_spaces` spaces.

    This is necessary until https://github.com/Textualize/rich/issues/2944 is resolved
    to ensure that tests succeed while running in `tox` on Windows.
    """
    return re.sub(rf"\s{{{max_spaces},}}", " " * max_spaces, text)


@pytest.mark.parametrize(
    "show, message, expected_console_output",
    [
        (True, "a line of output", "a line of output\n"),
        (False, "a line of output", ""),
    ],
)
def test_call(capsys, printer, message, show, expected_console_output):
    """Printer prints to console and log appropriately."""
    printer(message, show=show, stack_offset=1)
    assert capsys.readouterr().out == expected_console_output
    log = printer.export_log()
    assert len(log.splitlines()) == 1
    # The number of spaces in not consistent on Windows
    assert norm_sp(" " + message + " " * 139 + "console.py") in norm_sp(log)


def test_to_console(capsys, printer):
    """Printer prints only to console."""
    printer.to_console("a line of output")
    assert capsys.readouterr().out == "a line of output\n"
    assert printer.export_log() == ""


def test_to_log(capsys, printer):
    """Printer prints only to log."""
    printer.to_log("a line of output", stack_offset=1)
    assert capsys.readouterr().out == ""
    log = printer.export_log()
    assert len(log.splitlines()) == 1
    # The number of spaces in not consistent on Windows
    assert norm_sp(" a line of output" + " " * 139 + "console.py") in norm_sp(log)


def test_very_long_line(capsys, printer):
    """Very long lines are split."""
    printer.to_log("A very long line of output!! " * 6, stack_offset=1)
    assert capsys.readouterr().out == ""
    log = printer.export_log()
    assert len(log.splitlines()) == 2
    # The number of spaces in not consistent on Windows
    assert norm_sp(
        " " + "A very long line of output!! " * 5 + "A very    console.py:",
        max_spaces=3,
    ) in norm_sp(log, max_spaces=3)
    assert norm_sp(" long line of output!!" + " " * 148) in norm_sp(log)
