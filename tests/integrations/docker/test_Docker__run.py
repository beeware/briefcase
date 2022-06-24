import os
import sys
from unittest.mock import ANY

import pytest

from briefcase.console import Log


def test_simple_call(mock_docker, tmp_path, capsys):
    """A simple call will be invoked."""

    mock_docker.run(["hello", "world"])

    mock_docker._subprocess._subprocess.run.assert_called_with(
        [
            "docker",
            "run",
            "--tty",
            "--volume",
            f"{tmp_path / 'platform'}:/app:z",
            "--volume",
            f"{tmp_path / '.briefcase'}:/home/brutus/.briefcase:z",
            "briefcase/com.example.myapp:py3.X",
            "hello",
            "world",
        ],
        text=True,
        encoding=ANY,
    )
    assert capsys.readouterr().out == ""


def test_simple_call_with_arg(mock_docker, tmp_path, capsys):
    """Any extra keyword arguments are passed through as-is."""

    mock_docker.run(["hello", "world"], universal_newlines=True)

    mock_docker._subprocess._subprocess.run.assert_called_with(
        [
            "docker",
            "run",
            "--tty",
            "--volume",
            f"{tmp_path / 'platform'}:/app:z",
            "--volume",
            f"{tmp_path / '.briefcase'}:/home/brutus/.briefcase:z",
            "briefcase/com.example.myapp:py3.X",
            "hello",
            "world",
        ],
        universal_newlines=True,
        encoding=ANY,
    )
    assert capsys.readouterr().out == ""


def test_simple_call_with_path_arg(mock_docker, tmp_path, capsys):
    """Path-based arguments are converted to strings and passed in as-is."""

    mock_docker.run(["hello", tmp_path / "location"], cwd=tmp_path / "cwd")

    mock_docker._subprocess._subprocess.run.assert_called_with(
        [
            "docker",
            "run",
            "--tty",
            "--volume",
            f"{tmp_path / 'platform'}:/app:z",
            "--volume",
            f"{tmp_path / '.briefcase'}:/home/brutus/.briefcase:z",
            "briefcase/com.example.myapp:py3.X",
            "hello",
            os.fsdecode(tmp_path / "location"),
        ],
        cwd=os.fsdecode(tmp_path / "cwd"),
        text=True,
        encoding=ANY,
    )
    assert capsys.readouterr().out == ""


def test_simple_call_with_sys_executable_arg(
    mock_docker, tmp_path, capsys, monkeypatch
):
    """Filepath arg that are same as sys.executable are replaced with
    unqualified python[ver]"""

    test_python_path = "/path/to/python"
    monkeypatch.setattr("sys.executable", "/path/to/python")

    mock_docker.run(["hello", test_python_path])

    mock_docker._subprocess._subprocess.run.assert_called_with(
        [
            "docker",
            "run",
            "--tty",
            "--volume",
            f"{tmp_path / 'platform'}:/app:z",
            "--volume",
            f"{tmp_path / '.briefcase'}:/home/brutus/.briefcase:z",
            "briefcase/com.example.myapp:py3.X",
            "hello",
            "python3.X",
        ],
        text=True,
        encoding=ANY,
    )

    assert capsys.readouterr().out == ""


@pytest.mark.skipif(
    sys.platform == "win32", reason="Windows paths aren't converted in Docker context"
)
def test_simple_verbose_call(mock_docker, tmp_path, capsys):
    """If verbosity is turned out, there is output."""
    mock_docker.command.logger = Log(verbosity=2)

    mock_docker.run(["hello", "world"])

    mock_docker._subprocess._subprocess.run.assert_called_with(
        [
            "docker",
            "run",
            "--tty",
            "--volume",
            f"{tmp_path / 'platform'}:/app:z",
            "--volume",
            f"{tmp_path / '.briefcase'}:/home/brutus/.briefcase:z",
            "briefcase/com.example.myapp:py3.X",
            "hello",
            "world",
        ],
        text=True,
        encoding=ANY,
    )
    assert capsys.readouterr().out == (
        "\n"
        ">>> Running Command:\n"
        ">>>     docker run --tty "
        f"--volume {tmp_path / 'platform'}:/app:z "
        f"--volume {tmp_path / '.briefcase'}:/home/brutus/.briefcase:z "
        "briefcase/com.example.myapp:py3.X "
        "hello world\n"
        ">>> Return code: 3\n"
    )
