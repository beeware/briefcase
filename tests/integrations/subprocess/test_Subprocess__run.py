import os
from subprocess import CalledProcessError

import pytest

from briefcase.console import Log


def test_simple_call(mock_sub, capsys):
    "A simple call will be invoked"

    mock_sub.run(['hello', 'world'])

    mock_sub._subprocess.run.assert_called_with(['hello', 'world'])
    assert capsys.readouterr().out == ""


def test_simple_call_with_arg(mock_sub, capsys):
    "Any extra keyword arguments are passed through as-is"

    mock_sub.run(['hello', 'world'], universal_newlines=True)

    mock_sub._subprocess.run.assert_called_with(
        ['hello', 'world'],
        universal_newlines=True
    )
    assert capsys.readouterr().out == ""


def test_simple_call_with_path_arg(mock_sub, capsys, tmp_path):
    "Path-based arguments are converted to strings andpassed in as-is"

    mock_sub.run(['hello', tmp_path / 'location'], cwd=tmp_path / 'cwd')

    mock_sub._subprocess.run.assert_called_with(
        ['hello', os.fsdecode(tmp_path / 'location')],
        cwd=os.fsdecode(tmp_path / 'cwd')
    )
    assert capsys.readouterr().out == ""


def test_simple_debug_call(mock_sub, capsys):
    "If verbosity is turned out, there is output"
    mock_sub.command.logger = Log(verbosity=2)

    mock_sub.run(['hello', 'world'])

    mock_sub._subprocess.run.assert_called_with(['hello', 'world'])
    assert capsys.readouterr().out == ">>> \n>>> Running Command:\n>>>     hello world\n"


def test_simple_deep_debug_call(mock_sub, capsys):
    "If verbosity is turned out, there is output"
    mock_sub.command.logger = Log(verbosity=3)

    mock_sub.run(["hello", "world"])

    mock_sub._subprocess.run.assert_called_with(["hello", "world"])

    expected_output = """>>> 
>>> Running Command:
>>>     hello world
>>> Environment:
>>>     VAR1=Value 1
>>>     PS1=
>>> Line 2
>>> 
>>> Line 4
>>>     PWD=/home/user/
>>> Return code: 0
"""

    assert capsys.readouterr().out == expected_output


def test_calledprocesserror_exception_logging(mock_sub, capsys):
    mock_sub.command.logger = Log(verbosity=3)

    called_process_error = CalledProcessError(
        returncode=-1,
        cmd="hello world",
        output="output line 1\noutput line 2",
        stderr="error line 1\nerror line 2",
    )
    mock_sub._subprocess.run.side_effect = called_process_error

    with pytest.raises(CalledProcessError):
        mock_sub.run(["hello", "world"])

    expected_output = """>>> 
>>> Running Command:
>>>     hello world
>>> Environment:
>>>     VAR1=Value 1
>>>     PS1=
>>> Line 2
>>> 
>>> Line 4
>>>     PWD=/home/user/
>>> Return code: -1
"""

    assert capsys.readouterr().out == expected_output
