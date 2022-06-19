from subprocess import CalledProcessError
from unittest.mock import Mock

from pytest import fixture, raises

from briefcase.__main__ import main
from briefcase.console import Log
from briefcase.exceptions import BriefcaseCommandError


@fixture
def command(monkeypatch):
    command = Mock()
    command.logger = Log()
    monkeypatch.setattr("briefcase.__main__.parse_cmdline", lambda argv: (command, {}))
    return command


def test_no_cause(command, capsys):
    """A BriefcaseError is logged, and does not print a stack trace."""
    e = BriefcaseCommandError("error message")
    command.side_effect = e

    with raises(SystemExit):
        main()
    assert capsys.readouterr() == ("\nerror message\n", "")


def test_cpe_cause(command, capsys):
    """A BriefcaseError caused by a CalledProcessError logs the subprocess
    details."""
    e = BriefcaseCommandError("error message")
    command.side_effect = e
    cpe = CalledProcessError(1, ["command", "arg1"])
    expected_out = (
        "\nRunning Command:\n"
        "    command arg1\n"
        "Return code: 1\n"
        "\n"
        "error message\n"
    )

    e.__cause__ = cpe
    with raises(SystemExit):
        main()
    assert capsys.readouterr() == (expected_out, "")

    e.__cause__ = None
    e.__context__ = cpe
    with raises(SystemExit):
        main()
    assert capsys.readouterr() == (expected_out, "")


def test_other_cause(command, capsys):
    """A BriefcaseError caused by any other exception does not log the
    cause."""
    e = BriefcaseCommandError("error message")
    command.side_effect = e
    ve = ValueError("we have a problem")

    e.__cause__ = ve
    with raises(SystemExit):
        main()
    assert capsys.readouterr() == ("\nerror message\n", "")

    e.__cause__ = None
    e.__context__ = ve
    with raises(SystemExit):
        main()
    assert capsys.readouterr() == ("\nerror message\n", "")


def test_cpe_output(command, capsys):
    """CalledProcessError stdout and stderr is logged."""
    e = BriefcaseCommandError("error message")
    command.side_effect = e
    cpe = CalledProcessError(
        1,
        ["command", "arg1"],
        output="out line 1\nout line 2\n",
        stderr="err line 1\nerr line 2\n",
    )
    expected_out = (
        "\nRunning Command:\n"
        "    command arg1\n"
        "Command Output:\n"
        "    out line 1\n"
        "    out line 2\n"
        "Command Error Output (stderr):\n"
        "    err line 1\n"
        "    err line 2\n"
        "Return code: 1\n"
        "\n"
        "error message\n"
    )
    e.__cause__ = cpe

    with raises(SystemExit):
        main()
    assert capsys.readouterr() == (expected_out, "")


def test_cpe_cmd_as_str(command, capsys):
    """CalledProcessError cmd as a single string is logged correctly."""
    e = BriefcaseCommandError("error message")
    command.side_effect = e
    cpe = CalledProcessError(2, "command as one string")
    expected_out = (
        "\nRunning Command:\n"
        "    command as one string\n"
        "Return code: 2\n"
        "\n"
        "error message\n"
    )
    e.__cause__ = cpe

    with raises(SystemExit):
        main()
    assert capsys.readouterr() == (expected_out, "")


def test_cpe_cmd_with_spaces(command, capsys):
    """CalledProcessError arguments with spaces are quoted in the log."""
    e = BriefcaseCommandError("error message")
    command.side_effect = e
    cpe = CalledProcessError(3, ["command2", "two words"])
    expected_out = (
        "\nRunning Command:\n"
        "    command2 'two words'\n"
        "Return code: 3\n"
        "\n"
        "error message\n"
    )
    e.__cause__ = cpe

    with raises(SystemExit):
        main()
    assert capsys.readouterr() == (expected_out, "")


def test_cpe_verbosity(command, capsys):
    """CalledProcessError is not logged a second time if verbosity is high."""
    e = BriefcaseCommandError("error message")
    command.side_effect = e
    cpe = CalledProcessError(1, ["command", "arg1"])
    e.__cause__ = cpe

    command.logger.verbosity = 2
    with raises(SystemExit):
        main()
    assert capsys.readouterr() == ("\nerror message\n", "")
