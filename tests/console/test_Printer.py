import pytest

from briefcase.console import Printer


@pytest.fixture
def printer():
    printer = Printer()
    # clear log; since Printer is a pseudo-singleton,
    # the log can contain existing entries.
    printer.export_log()
    return printer


def no_sp(text: str) -> str:
    """Remove spaces from text."""
    return text.replace(" ", "")


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
    # The number of spaces in not consistent on Windows.
    # Remove `no_sp()` when https://github.com/Textualize/rich/issues/2944 is resolved
    assert no_sp(" " + message + " " * 139 + "console.py") in no_sp(log)


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
    # The number of spaces in not consistent on Windows.
    # Remove `no_sp()` when https://github.com/Textualize/rich/issues/2944 is resolved
    assert no_sp(" a line of output" + " " * 139 + "console.py") in no_sp(log)


def test_very_long_line(capsys, printer):
    """Very long lines are split."""
    printer.to_log("A very long line of output!! " * 6, stack_offset=1)
    assert capsys.readouterr().out == ""
    log = printer.export_log()
    assert len(log.splitlines()) == 2
    # The number of spaces in not consistent on Windows.
    # Remove `no_sp()` when https://github.com/Textualize/rich/issues/2944 is resolved
    assert no_sp(
        " " + "A very long line of output!! " * 5 + "A very    console.py:"
    ) in no_sp(log)
    assert no_sp(" long line of output!!" + " " * 148) in no_sp(log)
