
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
        ['hello', str(tmp_path / 'location')],
        cwd=str(tmp_path / 'cwd')
    )
    assert capsys.readouterr().out == ""


def test_simple_verbose_call(mock_sub, capsys):
    "If verbosity is turned out, there is output"
    mock_sub.command.verbosity = 2

    mock_sub.run(['hello', 'world'])

    mock_sub._subprocess.run.assert_called_with(['hello', 'world'])
    assert capsys.readouterr().out == ">>> hello world\n"
