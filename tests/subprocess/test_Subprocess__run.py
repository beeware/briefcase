from unittest.mock import MagicMock

from briefcase.subprocess import Subprocess


def test_simple_call(capsys):
    "A simple call will be invoked"
    command = MagicMock()
    command.verbosity = 0

    sub = Subprocess(command)
    sub._subprocess = MagicMock()

    sub.run(['hello', 'world'])

    sub._subprocess.run.assert_called_with(['hello', 'world'])
    assert capsys.readouterr().out == ""


def test_simple_call_with_arg(capsys):
    "Any extra keyword arguments are passed through as-is"
    command = MagicMock()
    command.verbosity = 0

    sub = Subprocess(command)
    sub._subprocess = MagicMock()

    sub.run(['hello', 'world'], universal_newlines=True)

    sub._subprocess.run.assert_called_with(
        ['hello', 'world'],
        universal_newlines=True
    )
    assert capsys.readouterr().out == ""


def test_simple_call_with_path_arg(capsys, tmp_path):
    "Path-based arguments are converted to strings andpassed in as-is"
    command = MagicMock()
    command.verbosity = 0

    sub = Subprocess(command)
    sub._subprocess = MagicMock()

    sub.run(['hello', tmp_path / 'location'], cwd=tmp_path / 'cwd')

    sub._subprocess.run.assert_called_with(
        ['hello', str(tmp_path / 'location')],
        cwd=str(tmp_path / 'cwd')
    )
    assert capsys.readouterr().out == ""


def test_simple_verbose_call(capsys):
    "If verbosity is turned out, there is output"
    command = MagicMock()
    command.verbosity = 2

    sub = Subprocess(command)
    sub._subprocess = MagicMock()

    sub.run(['hello', 'world'])

    sub._subprocess.run.assert_called_with(['hello', 'world'])
    assert capsys.readouterr().out == ">>> hello world\n"
