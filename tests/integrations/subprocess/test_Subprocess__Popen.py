import os

from briefcase.console import Log


def test_simple_call(mock_sub, capsys):
    "A simple call will be invoked"

    mock_sub.Popen(['hello', 'world'])

    mock_sub._subprocess.Popen.assert_called_with(['hello', 'world'])
    assert capsys.readouterr().out == ""


def test_simple_call_with_arg(mock_sub, capsys):
    "Any extra keyword arguments are passed through as-is"

    mock_sub.Popen(['hello', 'world'], universal_newlines=True)

    mock_sub._subprocess.Popen.assert_called_with(
        ['hello', 'world'],
        universal_newlines=True
    )
    assert capsys.readouterr().out == ""


def test_simple_call_with_path_arg(mock_sub, capsys, tmp_path):
    "Path-based arguments are converted to strings andpassed in as-is"

    mock_sub.Popen(['hello', tmp_path / 'location'], cwd=tmp_path / 'cwd')

    mock_sub._subprocess.Popen.assert_called_with(
        ['hello', os.fsdecode(tmp_path / 'location')],
        cwd=os.fsdecode(tmp_path / 'cwd')
    )
    assert capsys.readouterr().out == ""


def test_simple_debug_call(mock_sub, capsys):
    "If verbosity is turned out, there is output"
    mock_sub.command.logger = Log(verbosity=2)

    mock_sub.Popen(['hello', 'world'])

    mock_sub._subprocess.Popen.assert_called_with(['hello', 'world'])
    assert capsys.readouterr().out == ">>> \n>>> Running Command:\n>>>     hello world\n"


def test_simple_debug_call_with_env(mock_sub, capsys):
    "If verbosity is turned out, and injected env vars are included output"
    mock_sub.command.logger = Log(verbosity=2)

    env = {"NewVar": "NewVarValue"}
    mock_sub.Popen(['hello', 'world'], env=env)

    merged_env = mock_sub.command.os.environ.copy()
    merged_env.update(env)
    mock_sub._subprocess.Popen.assert_called_with(['hello', 'world'], env=merged_env)

    expected_output = (
        ">>> \n"
        ">>> Running Command:\n"
        ">>>     hello world\n"
        ">>> Environment:\n"
        ">>>     NewVar=NewVarValue\n"
    )

    assert capsys.readouterr().out == expected_output


def test_simple_deep_debug_call(mock_sub, capsys):
    "If verbosity is turned out, there is output"
    mock_sub.command.logger = Log(verbosity=3)

    mock_sub.Popen(["hello", "world"])

    mock_sub._subprocess.Popen.assert_called_with(["hello", "world"])

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
    )

    assert capsys.readouterr().out == expected_output
