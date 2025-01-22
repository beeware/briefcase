import re

import pytest

from briefcase.console import Console


@pytest.fixture
def console():
    console = Console()
    # clear log; since Printer is a pseudo-singleton,
    # the log can contain existing entries.
    console.export_log()
    return console


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
def test_print(capsys, console, message, show, expected_console_output):
    """Console prints to console and log appropriately."""
    console.print(message, show=show, stack_offset=1)
    assert capsys.readouterr().out == expected_console_output
    log = console.export_log()
    assert len(log.splitlines()) == 1
    # The number of spaces in not consistent on Windows
    assert norm_sp(" " + message + " " * 139 + "console.py") in norm_sp(log)


def test_to_console(capsys, console):
    """Console prints only to console."""
    console.to_console("a line of output")
    assert capsys.readouterr().out == "a line of output\n"
    assert console.export_log() == ""


def test_to_log(capsys, console):
    """Printer prints only to log."""
    console.to_log("a line of output", stack_offset=1)
    assert capsys.readouterr().out == ""
    log = console.export_log()
    assert len(log.splitlines()) == 1
    # The number of spaces in not consistent on Windows
    assert norm_sp(" a line of output" + " " * 139 + "console.py") in norm_sp(log)


def test_very_long_line(capsys, console):
    """Very long lines are split."""
    console.to_log("A very long line of output!! " * 6, stack_offset=1)
    assert capsys.readouterr().out == ""
    log = console.export_log()
    assert len(log.splitlines()) == 2
    # The number of spaces in not consistent on Windows
    assert norm_sp(
        " " + "A very long line of output!! " * 5 + "A very    console.py:",
        max_spaces=3,
    ) in norm_sp(log, max_spaces=3)
    assert norm_sp(" long line of output!!" + " " * 148) in norm_sp(log)
