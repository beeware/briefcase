import sys

import pytest


def test_simple_call(mock_docker, tmp_path, capsys):
    "A simple call will be invoked"

    mock_docker.run(['hello', 'world'])

    mock_docker._subprocess._subprocess.run.assert_called_with(
        [
            'docker',
            'run', '--tty',
            '--volume', '{platform_path}:/app:z'.format(
                platform_path=tmp_path / 'platform'
            ),
            '--volume', '{dot_briefcase_path}:/home/brutus/.briefcase:z'.format(
                dot_briefcase_path=tmp_path / '.briefcase'
            ),
            'briefcase/com.example.myapp:py3.X',
            'hello',
            'world'
        ]
    )
    assert capsys.readouterr().out == ""


def test_simple_call_with_arg(mock_docker, tmp_path, capsys):
    "Any extra keyword arguments are passed through as-is"

    mock_docker.run(['hello', 'world'], universal_newlines=True)

    mock_docker._subprocess._subprocess.run.assert_called_with(
        [
            'docker',
            'run', '--tty',
            '--volume', '{platform_path}:/app:z'.format(
                platform_path=tmp_path / 'platform'
            ),
            '--volume', '{dot_briefcase_path}:/home/brutus/.briefcase:z'.format(
                dot_briefcase_path=tmp_path / '.briefcase'
            ),
            'briefcase/com.example.myapp:py3.X',
            'hello',
            'world'
        ],
        universal_newlines=True
    )
    assert capsys.readouterr().out == ""


def test_simple_call_with_path_arg(mock_docker, tmp_path, capsys):
    "Path-based arguments are converted to strings andpassed in as-is"

    mock_docker.run(['hello', tmp_path / 'location'], cwd=tmp_path / 'cwd')

    mock_docker._subprocess._subprocess.run.assert_called_with(
        [
            'docker',
            'run',  '--tty',
            '--volume', '{platform_path}:/app:z'.format(
                platform_path=tmp_path / 'platform'
            ),
            '--volume', '{dot_briefcase_path}:/home/brutus/.briefcase:z'.format(
                dot_briefcase_path=tmp_path / '.briefcase'
            ),
            'briefcase/com.example.myapp:py3.X',
            'hello',
            str(tmp_path / 'location')
        ],
        cwd=str(tmp_path / 'cwd')
    )
    assert capsys.readouterr().out == ""


@pytest.mark.skipif(
    sys.platform == "win32",
    reason="Windows paths aren't converted in Docker context"
)
def test_simple_verbose_call(mock_docker, tmp_path, capsys):
    "If verbosity is turned out, there is output"
    mock_docker.command.verbosity = 2

    mock_docker.run(['hello', 'world'])

    mock_docker._subprocess._subprocess.run.assert_called_with(
        [
            'docker',
            'run', '--tty',
            '--volume', '{platform_path}:/app:z'.format(
                platform_path=tmp_path / 'platform'
            ),
            '--volume', '{dot_briefcase_path}:/home/brutus/.briefcase:z'.format(
                dot_briefcase_path=tmp_path / '.briefcase'
            ),
            'briefcase/com.example.myapp:py3.X',
            'hello',
            'world',
        ]
    )
    assert capsys.readouterr().out == (
        ">>> docker run --tty "
        "--volume {platform_path}:/app:z "
        "--volume {dot_briefcase_path}:/home/brutus/.briefcase:z "
        "briefcase/com.example.myapp:py3.X "
        "hello world\n"
    ).format(
        platform_path=tmp_path / 'platform',
        dot_briefcase_path=tmp_path / '.briefcase',
    )
