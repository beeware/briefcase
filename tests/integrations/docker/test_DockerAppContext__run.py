import os
import sys
from pathlib import Path

import pytest

from briefcase.console import LogLevel


def test_simple_call(mock_docker_app_context, tmp_path, sub_stream_kw, capsys):
    """A simple call will be invoked."""

    mock_docker_app_context.run(["hello", "world"])

    mock_docker_app_context.tools.subprocess._subprocess.Popen.assert_called_once_with(
        [
            "docker",
            "run",
            "--rm",
            "--volume",
            f"{tmp_path / 'bundle'}:/app:z",
            "--volume",
            f"{tmp_path / 'briefcase'}:/briefcase:z",
            "briefcase/com.example.myapp:py3.X",
            "hello",
            "world",
        ],
        **sub_stream_kw,
    )
    assert capsys.readouterr().out == (
        "\n"
        "Entering Docker context...\n"
        "Docker| ------------------------------------------------------------------\n"
        "Docker| ------------------------------------------------------------------\n"
        "Leaving Docker context.\n"
        "\n"
    )


def test_interactive(mock_docker_app_context, tmp_path, sub_kw, capsys):
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
            f"{tmp_path / 'bundle'}:/app:z",
            "--volume",
            f"{tmp_path / 'briefcase'}:/briefcase:z",
            "briefcase/com.example.myapp:py3.X",
            "hello",
            "world",
        ],
        **sub_kw,
    )
    assert capsys.readouterr().out == (
        "\n"
        "Entering Docker context...\n"
        "Docker| ------------------------------------------------------------------\n"
        "Docker| ------------------------------------------------------------------\n"
        "Leaving Docker context.\n"
        "\n"
    )


def test_extra_mounts(mock_docker_app_context, tmp_path, sub_stream_kw, capsys):
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
            f"{tmp_path / 'bundle'}:/app:z",
            "--volume",
            f"{tmp_path / 'briefcase'}:/briefcase:z",
            "--volume",
            "/path/to/first:/container/first:z",
            "--volume",
            "/path/to/second:/container/second:z",
            "briefcase/com.example.myapp:py3.X",
            "hello",
            "world",
        ],
        **sub_stream_kw,
    )
    assert capsys.readouterr().out == (
        "\n"
        "Entering Docker context...\n"
        "Docker| ------------------------------------------------------------------\n"
        "Docker| ------------------------------------------------------------------\n"
        "Leaving Docker context.\n"
        "\n"
    )


@pytest.mark.skipif(
    sys.platform == "win32", reason="Windows paths aren't converted in Docker context"
)
def test_cwd(mock_docker_app_context, tmp_path, sub_stream_kw, capsys):
    """A subprocess call can use a working directory relative to the project folder."""

    mock_docker_app_context.run(
        ["hello", "world"],
        cwd=tmp_path / "bundle/foobar",
    )

    mock_docker_app_context.tools.subprocess._subprocess.Popen.assert_called_once_with(
        [
            "docker",
            "run",
            "--rm",
            "--volume",
            f"{tmp_path / 'bundle'}:/app:z",
            "--volume",
            f"{tmp_path / 'briefcase'}:/briefcase:z",
            "--workdir",
            "/app/foobar",
            "briefcase/com.example.myapp:py3.X",
            "hello",
            "world",
        ],
        **sub_stream_kw,
    )
    assert capsys.readouterr().out == (
        "\n"
        "Entering Docker context...\n"
        "Docker| ------------------------------------------------------------------\n"
        "Docker| ------------------------------------------------------------------\n"
        "Leaving Docker context.\n"
        "\n"
    )


def test_call_with_arg_and_env(
    mock_docker_app_context,
    tmp_path,
    sub_stream_kw,
    capsys,
):
    """Extra keyword arguments are passed through as-is; env modifications are
    converted."""

    mock_docker_app_context.run(
        ["hello", "world"],
        env={
            "MAGIC": "True",
            "IMPORTANCE": "super high",
        },
        extra_kw="extra",
    )

    mock_docker_app_context.tools.subprocess._subprocess.Popen.assert_called_once_with(
        [
            "docker",
            "run",
            "--rm",
            "--volume",
            f"{tmp_path / 'bundle'}:/app:z",
            "--volume",
            f"{tmp_path / 'briefcase'}:/briefcase:z",
            "--env",
            "MAGIC=True",
            "--env",
            "IMPORTANCE=super high",
            "briefcase/com.example.myapp:py3.X",
            "hello",
            "world",
        ],
        extra_kw="extra",
        **sub_stream_kw,
    )
    assert capsys.readouterr().out == (
        "\n"
        "Entering Docker context...\n"
        "Docker| ------------------------------------------------------------------\n"
        "Docker| ------------------------------------------------------------------\n"
        "Leaving Docker context.\n"
        "\n"
    )


@pytest.mark.skipif(
    sys.platform == "win32", reason="Windows paths aren't converted in Docker context"
)
def test_call_with_path_arg_and_env(
    mock_docker_app_context,
    tmp_path,
    sub_stream_kw,
    capsys,
):
    """Path-based arguments and environment are converted to strings and passed in as-
    is."""

    mock_docker_app_context.run(
        ["hello", tmp_path / "location"],
        env={
            "MAGIC": "True",
            "PATH": f"/somewhere/safe:{tmp_path / 'briefcase' / 'tools'}:{tmp_path / 'bundle' / 'location'}",
        },
        cwd=tmp_path / "cwd",
    )

    mock_docker_app_context.tools.subprocess._subprocess.Popen.assert_called_once_with(
        [
            "docker",
            "run",
            "--rm",
            "--volume",
            f"{tmp_path / 'bundle'}:/app:z",
            "--volume",
            f"{tmp_path / 'briefcase'}:/briefcase:z",
            "--env",
            "MAGIC=True",
            "--env",
            "PATH=/somewhere/safe:/briefcase/tools:/app/location",
            "--workdir",
            f"{tmp_path / 'cwd'}",
            "briefcase/com.example.myapp:py3.X",
            "hello",
            os.fsdecode(tmp_path / "location"),
        ],
        **sub_stream_kw,
    )
    assert capsys.readouterr().out == (
        "\n"
        "Entering Docker context...\n"
        "Docker| ------------------------------------------------------------------\n"
        "Docker| ------------------------------------------------------------------\n"
        "Leaving Docker context.\n"
        "\n"
    )


@pytest.mark.skipif(
    sys.platform == "win32", reason="Windows paths aren't converted in Docker context"
)
def test_interactive_with_path_arg_and_env_and_mounts(
    mock_docker_app_context,
    tmp_path,
    sub_kw,
    capsys,
):
    """Docker can be invoked in interactive mode with all the extras."""
    mock_docker_app_context.run(
        ["hello", tmp_path / "location"],
        env={
            "MAGIC": "True",
            "PATH": f"/somewhere/safe:{tmp_path / 'briefcase' / 'tools'}:{tmp_path / 'bundle' / 'location'}",
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
            f"{tmp_path / 'bundle'}:/app:z",
            "--volume",
            f"{tmp_path / 'briefcase'}:/briefcase:z",
            "--volume",
            "/path/to/first:/container/first:z",
            "--volume",
            "/path/to/second:/container/second:z",
            "--env",
            "MAGIC=True",
            "--env",
            "PATH=/somewhere/safe:/briefcase/tools:/app/location",
            "--workdir",
            f"{tmp_path / 'cwd'}",
            "briefcase/com.example.myapp:py3.X",
            "hello",
            os.fsdecode(tmp_path / "location"),
        ],
        **sub_kw,
    )
    assert capsys.readouterr().out == (
        "\n"
        "Entering Docker context...\n"
        "Docker| ------------------------------------------------------------------\n"
        "Docker| ------------------------------------------------------------------\n"
        "Leaving Docker context.\n"
        "\n"
    )


@pytest.mark.skipif(
    sys.platform == "win32", reason="Windows paths aren't converted in Docker context"
)
def test_simple_verbose_call(mock_docker_app_context, tmp_path, sub_stream_kw, capsys):
    """If verbosity is turned out, there is output."""
    mock_docker_app_context.tools.logger.verbosity = LogLevel.DEBUG

    mock_docker_app_context.run(["hello", "world"])

    mock_docker_app_context.tools.subprocess._subprocess.Popen.assert_called_once_with(
        [
            "docker",
            "run",
            "--rm",
            "--volume",
            f"{tmp_path / 'bundle'}:/app:z",
            "--volume",
            f"{tmp_path / 'briefcase'}:/briefcase:z",
            "briefcase/com.example.myapp:py3.X",
            "hello",
            "world",
        ],
        **sub_stream_kw,
    )
    assert capsys.readouterr().out == (
        "\n"
        "Entering Docker context...\n"
        "Docker| ------------------------------------------------------------------\n"
        "Docker| \n"
        "Docker| >>> Running Command:\n"
        "Docker| >>>     docker run "
        "--rm "
        f"--volume {tmp_path / 'bundle'}:/app:z "
        f"--volume {tmp_path / 'briefcase'}:/briefcase:z "
        "briefcase/com.example.myapp:py3.X "
        "hello world\n"
        "Docker| >>> Working Directory:\n"
        f"Docker| >>>     {Path.cwd()}\n"
        "Docker| >>> Return code: 0\n"
        "Docker| ------------------------------------------------------------------\n"
        "Leaving Docker context.\n"
        "\n"
    )
