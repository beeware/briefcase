import os

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

    expected_output = ">>> \n>>> Running Command:\n>>>     hello world\n>>> Environment:"
    # some env vars (eg PS1) can contain line breaks...so this tries to replicate
    # Log._log()'s functionality to print multi-line content with the appropriate preface.
    for env_var, value in os.environ.items():
        expected_output += "\n>>>     "
        expected_output += "\n>>> ".join(f"{env_var}={value}".splitlines())
    expected_output += "\n>>> Return code: 0\n"

    assert capsys.readouterr().out == expected_output
