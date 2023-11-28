import os
import sys
from pathlib import Path

import pytest

from briefcase.console import LogLevel


def test_simple_call(mock_docker_app_context, tmp_path, sub_check_output_kw, capsys):
    """A simple call will be invoked."""
    assert mock_docker_app_context.check_output(["hello", "world"]) == "goodbye\n"

    mock_docker_app_context.tools.subprocess._subprocess.check_output.assert_called_once_with(
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
        **sub_check_output_kw,
    )
    assert capsys.readouterr().out == ""


def test_extra_mounts(mock_docker_app_context, tmp_path, sub_check_output_kw, capsys):
    """A call can request additional mounts."""
    assert (
        mock_docker_app_context.check_output(
            ["hello", "world"],
            mounts=[
                ("/path/to/first", "/container/first"),
                ("/path/to/second", "/container/second"),
            ],
        )
        == "goodbye\n"
    )

    mock_docker_app_context.tools.subprocess._subprocess.check_output.assert_called_once_with(
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
        **sub_check_output_kw,
    )
    assert capsys.readouterr().out == ""


@pytest.mark.skipif(
    sys.platform == "win32", reason="Windows paths aren't converted in Docker context"
)
def test_cwd(mock_docker_app_context, tmp_path, sub_check_output_kw, capsys):
    """A call can use a working directory relative to the project folder."""
    assert (
        mock_docker_app_context.check_output(
            ["hello", "world"],
            cwd=tmp_path / "bundle/foobar",
        )
        == "goodbye\n"
    )

    mock_docker_app_context.tools.subprocess._subprocess.check_output.assert_called_once_with(
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
        **sub_check_output_kw,
    )
    assert capsys.readouterr().out == ""


def test_call_with_arg_and_env(
    mock_docker_app_context,
    tmp_path,
    sub_check_output_kw,
    capsys,
):
    """Extra keyword arguments are passed through as-is; env modifications are
    converted."""
    output = mock_docker_app_context.check_output(
        ["hello", "world"],
        env={
            "MAGIC": "True",
            "IMPORTANCE": "super high",
        },
        extra_kw="extra",
    )
    assert output == "goodbye\n"

    mock_docker_app_context.tools.subprocess._subprocess.check_output.assert_called_once_with(
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
        **sub_check_output_kw,
    )
    assert capsys.readouterr().out == ""


@pytest.mark.skipif(
    sys.platform == "win32",
    reason="Windows paths aren't converted in Docker context",
)
def test_call_with_path_arg_and_env(
    mock_docker_app_context,
    tmp_path,
    sub_check_output_kw,
    capsys,
):
    """Path-based arguments and environment are converted to strings and passed in as-
    is."""
    output = mock_docker_app_context.check_output(
        ["hello", tmp_path / "location"],
        env={
            "MAGIC": "True",
            "PATH": f"/somewhere/safe:{tmp_path / 'briefcase' / 'tools'}:{tmp_path / 'bundle' / 'location'}",
        },
        cwd=tmp_path / "cwd",
    )
    assert output == "goodbye\n"

    mock_docker_app_context.tools.subprocess._subprocess.check_output.assert_called_once_with(
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
        **sub_check_output_kw,
    )
    assert capsys.readouterr().out == ""


@pytest.mark.skipif(
    sys.platform == "win32", reason="Windows paths aren't converted in Docker context"
)
def test_simple_verbose_call(
    mock_docker_app_context,
    tmp_path,
    sub_check_output_kw,
    capsys,
):
    """If verbosity is turned out, there is output."""
    mock_docker_app_context.tools.logger.verbosity = LogLevel.DEBUG

    assert mock_docker_app_context.check_output(["hello", "world"]) == "goodbye\n"

    mock_docker_app_context.tools.subprocess._subprocess.check_output.assert_called_once_with(
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
        **sub_check_output_kw,
    )
    assert capsys.readouterr().out == (
        "\n"
        ">>> Running Command:\n"
        ">>>     docker run "
        "--rm "
        f"--volume {tmp_path / 'bundle'}:/app:z "
        f"--volume {tmp_path / 'briefcase'}:/briefcase:z "
        "briefcase/com.example.myapp:py3.X "
        "hello world\n"
        ">>> Working Directory:\n"
        f">>>     {Path.cwd()}\n"
        ">>> Command Output:\n"
        ">>>     goodbye\n"
        ">>> Return code: 0\n"
    )
