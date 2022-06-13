import pytest

from briefcase.console import Printer


@pytest.fixture
def printer():
    printer = Printer()
    # clear log; since Printer is a pseudo-singleton,
    # the log can contain existing entries.
    printer.export_log()
    return printer


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
    assert message + " " * 79 + "console.py" in log


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
    assert "a line of output" + " " * 79 + "console.py" in log
