import argparse

import pytest


def test_parse_options(base_command):
    "Command line options are parsed if provided"
    parser = argparse.ArgumentParser(prog='briefcase')
    base_command.parse_options(
        parser=parser,
        extra=(
            '-x', 'wibble',
            '-r', 'important'
        )
    )

    assert base_command.options.extra == "wibble"
    assert base_command.options.mystery is None
    assert base_command.options.required == "important"


def test_missing_option(base_command, capsys):
    "If a required option isn't provided, an error is raised"
    parser = argparse.ArgumentParser(prog='briefcase')
    with pytest.raises(SystemExit) as excinfo:
        base_command.parse_options(
            parser=parser,
            extra=('-x', 'wibble')
        )

    # Error code for a missing required option
    assert excinfo.value.code == 2
    # Error message about missing option is displayed
    err = capsys.readouterr().err
    assert "the following arguments are required: -r/--required" in err


def test_unknown_option(other_command, capsys):
    "If an unknown command is provided, it rasises an error"
    parser = argparse.ArgumentParser(prog='briefcase')
    with pytest.raises(SystemExit) as excinfo:
        other_command.parse_options(
            parser=parser,
            extra=('-y', 'because')
        )

    # Error code for a unknown option
    assert excinfo.value.code == 2
    # Error message about unknown option is displayed
    err = capsys.readouterr().err
    assert "unrecognized arguments: -y because" in err


def test_no_options(other_command, capsys):
    "If a command doesn't define options, any option is an error"
    parser = argparse.ArgumentParser(prog='briefcase')
    with pytest.raises(SystemExit) as excinfo:
        other_command.parse_options(
            parser=parser,
            extra=('-x', 'wibble')
        )

    # Error code for a unknown option
    assert excinfo.value.code == 2
    # Error message about unknown option is displayed
    err = capsys.readouterr().err
    assert "unrecognized arguments: -x wibble" in err
