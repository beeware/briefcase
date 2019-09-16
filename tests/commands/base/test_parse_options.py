import argparse

import pytest

from briefcase.commands.base import BaseCommand


class DummyCommand(BaseCommand):
    """
    A dummy command to test the BaseCommand interface.

    Defines a mix of configuration options.
    """
    def __init__(self):
        super().__init__(platform='tester', output_format='dummy')

    def add_options(self, parser):
        # Provide some extra arguments:
        # * some optional arguments
        parser.add_argument('-x', '--extra')
        parser.add_argument('-m', '--mystery')
        # * a required argument
        parser.add_argument('-r', '--required', required=True)

    def bundle_path(self, app, base=None):
        raise NotImplementedError()

    def binary_path(self, app, base=None):
        raise NotImplementedError()


def test_parse_options():
    "Command line options are parsed if provided"
    command = DummyCommand()
    parser = argparse.ArgumentParser(prog='briefcase')
    command.parse_options(
        parser=parser,
        extra=(
            '-x', 'wibble',
            '-r', 'important'
        )
    )

    assert command.options.extra == "wibble"
    assert command.options.mystery is None
    assert command.options.required == "important"


def test_missing_option(capsys):
    "If a required"
    command = DummyCommand()
    parser = argparse.ArgumentParser(prog='briefcase')
    with pytest.raises(SystemExit) as excinfo:
        command.parse_options(
            parser=parser,
            extra=('-x', 'wibble')
        )

    # Error code for a missing required option
    assert excinfo.value.code == 2
    # Error message about missing option is displayed
    err = capsys.readouterr().err
    assert "the following arguments are required: -r/--required" in err
