import os
from subprocess import CalledProcessError

import pytest

from briefcase.console import Log


def test_simple_call(mock_sub, capsys):
    "A simple call will be invoked"

    mock_sub.check_output(['hello', 'world'])

    mock_sub._subprocess.check_output.assert_called_with(['hello', 'world'])
    assert capsys.readouterr().out == ""


def test_simple_call_with_arg(mock_sub, capsys):
    "Any extra keyword arguments are passed through as-is"

    mock_sub.check_output(['hello', 'world'], universal_newlines=True)

    mock_sub._subprocess.check_output.assert_called_with(
        ['hello', 'world'],
        universal_newlines=True
    )
    assert capsys.readouterr().out == ""


def test_simple_call_with_path_arg(mock_sub, capsys, tmp_path):
    "Path-based arguments are converted to strings andpassed in as-is"

    mock_sub.check_output(['hello', tmp_path / 'location'], cwd=tmp_path / 'cwd')

    mock_sub._subprocess.check_output.assert_called_with(
        ['hello', os.fsdecode(tmp_path / 'location')],
        cwd=os.fsdecode(tmp_path / 'cwd')
    )
    assert capsys.readouterr().out == ""


def test_simple_debug_call(mock_sub, capsys):
    "If verbosity is turned out, there is output"
    mock_sub.command.logger = Log(verbosity=2)

    mock_sub.check_output(['hello', 'world'])

    mock_sub._subprocess.check_output.assert_called_with(['hello', 'world'])

    assert capsys.readouterr().out == ">>> \n>>> Running Command:\n>>>     hello world\n"


def test_simple_deep_debug_call(mock_sub, capsys):
    "If verbosity is turned out, there is output"
    mock_sub.command.logger = Log(verbosity=3)

    mock_sub.check_output(["hello", "world"])

    mock_sub._subprocess.check_output.assert_called_with(["hello", "world"])

    expected_output = (
        ">>> \n"
        ">>> Running Command:\n"
        ">>>     hello world\n"
        ">>> Full Environment:\n"
        ">>>     VAR1=Value 1\n"
        ">>>     PS1=\n"
        ">>> Line 2\n"
        ">>> \n"
        ">>> Line 4\n"
        ">>>     PWD=/home/user/\n"
        ">>> Command Output:\n"
        ">>>     some output line 1\n"
        ">>>     more output line 2\n"
        ">>> Return code: 0\n"
    )

    assert capsys.readouterr().out == expected_output


def test_calledprocesserror_exception_logging(mock_sub, capsys):
    mock_sub.command.logger = Log(verbosity=3)

    called_process_error = CalledProcessError(
        returncode=-1,
        cmd="hello world",
        output="output line 1\noutput line 2",
        stderr="error line 1\nerror line 2",
    )
    mock_sub._subprocess.check_output.side_effect = called_process_error

    with pytest.raises(CalledProcessError):
        mock_sub.check_output(["hello", "world"])

    expected_output = (
        ">>> \n"
        ">>> Running Command:\n"
        ">>>     hello world\n"
        ">>> Full Environment:\n"
        ">>>     VAR1=Value 1\n"
        ">>>     PS1=\n"
        ">>> Line 2\n"
        ">>> \n"
        ">>> Line 4\n"
        ">>>     PWD=/home/user/\n"
        ">>> Command Output:\n"
        ">>>     output line 1\n"
        ">>>     output line 2\n"
        ">>> Command Error Output (stderr):\n"
        ">>>     error line 1\n"
        ">>>     error line 2\n"
        ">>> Return code: -1\n"
    )

    assert capsys.readouterr().out == expected_output
