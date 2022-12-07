import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import ANY

import pytest


def test_simple_call(mock_docker_app_context, tmp_path, capsys):
    """A simple call will be invoked."""

    mock_docker_app_context.run(["hello", "world"])

    mock_docker_app_context.tools.subprocess._subprocess.Popen.assert_called_once_with(
        [
            "docker",
            "run",
            "--rm",
            "--volume",
            f"{tmp_path / 'platform'}:/app:z",
            "--volume",
            f"{tmp_path / 'briefcase'}:/home/brutus/.cache/briefcase:z",
            "briefcase/com.example.myapp:py3.X",
            "hello",
            "world",
        ],
        text=True,
        encoding=ANY,
        bufsize=1,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    assert capsys.readouterr().out == (
        "\n"
        "[myapp] Entering Docker context...\n"
        "\n"
        "[myapp] Leaving Docker context\n"
    )


def test_interactive(mock_docker_app_context, tmp_path, capsys):
    """Docker can be invoked in interactive mode."""
    mock_docker_app_context.run(["hello", "world"], interactive=True)

    # Interactive means the call to run is direct, rather than going through Popen
    mock_docker_app_context.tools.subprocess._subprocess.run.assert_called_once_with(
        [
            "docker",
            "run",
            "--rm",
            "-it",
            "--volume",
            f"{tmp_path / 'platform'}:/app:z",
            "--volume",
            f"{tmp_path / 'briefcase'}:/home/brutus/.cache/briefcase:z",
            "briefcase/com.example.myapp:py3.X",
            "hello",
            "world",
        ],
        text=True,
        encoding=ANY,
    )
    assert capsys.readouterr().out == (
        "\n"
        "[myapp] Entering Docker context...\n"
        "\n"
        "[myapp] Leaving Docker context\n"
    )


def test_extra_mounts(mock_docker_app_context, tmp_path, capsys):
    """A subprocess call can be augmented with mounts."""

    mock_docker_app_context.run(
        ["hello", "world"],
        mounts=[
            ("/path/to/first", "/container/first"),
            ("/path/to/second", "/container/second"),
        ],
    )

    mock_docker_app_context.tools.subprocess._subprocess.Popen.assert_called_once_with(
        [
            "docker",
            "run",
            "--rm",
            "--volume",
            f"{tmp_path / 'platform'}:/app:z",
            "--volume",
            f"{tmp_path / 'briefcase'}:/home/brutus/.cache/briefcase:z",
            "--volume",
            "/path/to/first:/container/first:z",
            "--volume",
            "/path/to/second:/container/second:z",
            "briefcase/com.example.myapp:py3.X",
            "hello",
            "world",
        ],
        text=True,
        encoding=ANY,
        bufsize=1,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    assert capsys.readouterr().out == (
        "\n"
        "[myapp] Entering Docker context...\n"
        "\n"
        "[myapp] Leaving Docker context\n"
    )


def test_call_with_arg_and_env(mock_docker_app_context, tmp_path, capsys):
    """Extra keyword arguments are passed through as-is; env modifications are
    converted."""

    mock_docker_app_context.run(
        ["hello", "world"],
        env={
            "MAGIC": "True",
            "IMPORTANCE": "super high",
        },
        universal_newlines=True,
    )

    mock_docker_app_context.tools.subprocess._subprocess.Popen.assert_called_once_with(
        [
            "docker",
            "run",
            "--rm",
            "--volume",
            f"{tmp_path / 'platform'}:/app:z",
            "--volume",
            f"{tmp_path / 'briefcase'}:/home/brutus/.cache/briefcase:z",
            "--env",
            "MAGIC=True",
            "--env",
            "IMPORTANCE=super high",
            "briefcase/com.example.myapp:py3.X",
            "hello",
            "world",
        ],
        universal_newlines=True,
        encoding=ANY,
        bufsize=1,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    assert capsys.readouterr().out == (
        "\n"
        "[myapp] Entering Docker context...\n"
        "\n"
        "[myapp] Leaving Docker context\n"
    )


@pytest.mark.skipif(
    sys.platform == "win32", reason="Windows paths aren't converted in Docker context"
)
def test_call_with_path_arg_and_env(mock_docker_app_context, tmp_path, capsys):
    """Path-based arguments and environment are converted to strings and passed
    in as-is."""

    mock_docker_app_context.run(
        ["hello", tmp_path / "location"],
        env={
            "MAGIC": "True",
            "PATH": f"/somewhere/safe:{tmp_path / 'briefcase' / 'tools'}:{tmp_path / 'platform' / 'location'}",
        },
        cwd=tmp_path / "cwd",
    )

    mock_docker_app_context.tools.subprocess._subprocess.Popen.assert_called_once_with(
        [
            "docker",
            "run",
            "--rm",
            "--volume",
            f"{tmp_path / 'platform'}:/app:z",
            "--volume",
            f"{tmp_path / 'briefcase'}:/home/brutus/.cache/briefcase:z",
            "--env",
            "MAGIC=True",
            "--env",
            "PATH=/somewhere/safe:/home/brutus/.cache/briefcase/tools:/app/location",
            "briefcase/com.example.myapp:py3.X",
            "hello",
            os.fsdecode(tmp_path / "location"),
        ],
        cwd=os.fsdecode(tmp_path / "cwd"),
        text=True,
        encoding=ANY,
        bufsize=1,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    assert capsys.readouterr().out == (
        "\n"
        "[myapp] Entering Docker context...\n"
        "\n"
        "[myapp] Leaving Docker context\n"
    )


@pytest.mark.skipif(
    sys.platform == "win32", reason="Windows paths aren't converted in Docker context"
)
def test_interactive_with_path_arg_and_env_and_mounts(
    mock_docker_app_context, tmp_path, capsys
):
    """Docker can be invoked in interactive mode with all the extras."""
    mock_docker_app_context.run(
        ["hello", tmp_path / "location"],
        env={
            "MAGIC": "True",
            "PATH": f"/somewhere/safe:{tmp_path / 'briefcase' / 'tools'}:{tmp_path / 'platform' / 'location'}",
        },
        cwd=tmp_path / "cwd",
        interactive=True,
        mounts=[
            ("/path/to/first", "/container/first"),
            ("/path/to/second", "/container/second"),
        ],
    )

    # Interactive means the call to run is direct, rather than going through Popen
    mock_docker_app_context.tools.subprocess._subprocess.run.assert_called_once_with(
        [
            "docker",
            "run",
            "--rm",
            "-it",
            "--volume",
            f"{tmp_path / 'platform'}:/app:z",
            "--volume",
            f"{tmp_path / 'briefcase'}:/home/brutus/.cache/briefcase:z",
            "--volume",
            "/path/to/first:/container/first:z",
            "--volume",
            "/path/to/second:/container/second:z",
            "--env",
            "MAGIC=True",
            "--env",
            "PATH=/somewhere/safe:/home/brutus/.cache/briefcase/tools:/app/location",
            "briefcase/com.example.myapp:py3.X",
            "hello",
            os.fsdecode(tmp_path / "location"),
        ],
        cwd=os.fsdecode(tmp_path / "cwd"),
        text=True,
        encoding=ANY,
    )
    assert capsys.readouterr().out == (
        "\n"
        "[myapp] Entering Docker context...\n"
        "\n"
        "[myapp] Leaving Docker context\n"
    )


@pytest.mark.skipif(
    sys.platform == "win32", reason="Windows paths aren't converted in Docker context"
)
def test_simple_verbose_call(mock_docker_app_context, tmp_path, capsys):
    """If verbosity is turned out, there is output."""
    mock_docker_app_context.tools.logger.verbosity = 2

    mock_docker_app_context.run(["hello", "world"])

    mock_docker_app_context.tools.subprocess._subprocess.Popen.assert_called_once_with(
        [
            "docker",
            "run",
            "--rm",
            "--volume",
            f"{tmp_path / 'platform'}:/app:z",
            "--volume",
            f"{tmp_path / 'briefcase'}:/home/brutus/.cache/briefcase:z",
            "briefcase/com.example.myapp:py3.X",
            "hello",
            "world",
        ],
        text=True,
        encoding=ANY,
        bufsize=1,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    assert capsys.readouterr().out == (
        "\n"
        "[myapp] Entering Docker context...\n"
        "\n"
        ">>> Running Command:\n"
        ">>>     docker run "
        "--rm "
        f"--volume {tmp_path / 'platform'}:/app:z "
        f"--volume {tmp_path / 'briefcase'}:/home/brutus/.cache/briefcase:z "
        "briefcase/com.example.myapp:py3.X "
        "hello world\n"
        ">>> Working Directory:\n"
        f">>>     {Path.cwd()}\n"
        ">>> Return code: 0\n"
        "\n"
        "[myapp] Leaving Docker context\n"
    )
