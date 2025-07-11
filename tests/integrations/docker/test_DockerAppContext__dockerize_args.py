import os
import sys

import pytest


@pytest.mark.usefixtures("mock_docker")
@pytest.mark.usefixtures("mock_docker_app_context")
def test_dockerize_args(mock_tools, my_app, tmp_path):
    """A command to run in Docker is dockerized."""
    dockerize_args = mock_tools[my_app].app_context._dockerize_args(["hello", "world"])

    assert dockerize_args == {
        "args": [
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
        "env": {"DOCKER_CLI_HINTS": "false"},
    }


@pytest.mark.usefixtures("mock_docker")
@pytest.mark.usefixtures("mock_docker_app_context")
def test_dockerize_args_sys_executable(mock_tools, my_app, tmp_path):
    """A command to run in Docker using the current Python is dockerized."""
    dockerize_args = mock_tools[my_app].app_context._dockerize_args(
        [sys.executable, "-m", "pip"]
    )

    assert dockerize_args == {
        "args": [
            "docker",
            "run",
            "--rm",
            "--volume",
            f"{tmp_path / 'bundle'}:/app:z",
            "--volume",
            f"{tmp_path / 'briefcase'}:/briefcase:z",
            "briefcase/com.example.myapp:py3.X",
            "python3.X",
            "-m",
            "pip",
        ],
        "env": {"DOCKER_CLI_HINTS": "false"},
    }


@pytest.mark.usefixtures("mock_docker")
@pytest.mark.usefixtures("mock_docker_app_context")
def test_dockerize_args_mounts(mock_tools, my_app, tmp_path):
    """A command to run in Docker with mounts is dockerized."""
    dockerize_args = mock_tools[my_app].app_context._dockerize_args(
        ["hello", "world"],
        mounts=[
            ("/path/to/first", "/container/first"),
            ("/path/to/second", "/container/second"),
        ],
    )

    assert dockerize_args == {
        "args": [
            "docker",
            "run",
            "--rm",
            "--volume",
            "/path/to/first:/container/first:z",
            "--volume",
            "/path/to/second:/container/second:z",
            "--volume",
            f"{tmp_path / 'bundle'}:/app:z",
            "--volume",
            f"{tmp_path / 'briefcase'}:/briefcase:z",
            "briefcase/com.example.myapp:py3.X",
            "hello",
            "world",
        ],
        "env": {"DOCKER_CLI_HINTS": "false"},
    }


@pytest.mark.usefixtures("mock_docker")
@pytest.mark.usefixtures("mock_docker_app_context")
def test_dockerize_args_mounts_path(mock_tools, my_app, tmp_path):
    """A command to run in Docker with mounts and a path inside a mount is
    dockerized."""
    dockerize_args = mock_tools[my_app].app_context._dockerize_args(
        ["hello", "world", "/path/to/second/bin"],
        mounts=[
            ("/path/to/first", "/container/first"),
            ("/path/to/second", "/container/second"),
        ],
    )

    assert dockerize_args == {
        "args": [
            "docker",
            "run",
            "--rm",
            "--volume",
            "/path/to/first:/container/first:z",
            "--volume",
            "/path/to/second:/container/second:z",
            "--volume",
            f"{tmp_path / 'bundle'}:/app:z",
            "--volume",
            f"{tmp_path / 'briefcase'}:/briefcase:z",
            "briefcase/com.example.myapp:py3.X",
            "hello",
            "world",
            "/container/second/bin",
        ],
        "env": {"DOCKER_CLI_HINTS": "false"},
    }


@pytest.mark.skipif(
    sys.platform == "win32", reason="Windows paths aren't converted in Docker context"
)
@pytest.mark.usefixtures("mock_docker")
@pytest.mark.usefixtures("mock_docker_app_context")
def test_dockerize_args_cwd(mock_tools, my_app, tmp_path):
    """A command to run in Docker with a CWD is dockerized."""
    dockerize_args = mock_tools[my_app].app_context._dockerize_args(
        ["hello", "world"],
        cwd=tmp_path / "bundle/foobar",
    )

    assert dockerize_args == {
        "args": [
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
        "env": {"DOCKER_CLI_HINTS": "false"},
    }


@pytest.mark.usefixtures("mock_docker")
@pytest.mark.usefixtures("mock_docker_app_context")
def test_dockerize_args_arg_and_env(mock_tools, my_app, tmp_path):
    """A command to run in Docker with an extra keyword arg is dockerized."""
    dockerize_args = mock_tools[my_app].app_context._dockerize_args(
        ["hello", "world"],
        env={
            "MAGIC": "True",
            "IMPORTANCE": "super high",
        },
        check=True,
        steam_output=True,
    )

    assert dockerize_args == {
        "args": [
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
        "check": True,
        "steam_output": True,
        "env": {"DOCKER_CLI_HINTS": "false"},
    }


@pytest.mark.skipif(
    sys.platform == "win32", reason="Windows paths aren't converted in Docker context"
)
@pytest.mark.usefixtures("mock_docker")
@pytest.mark.usefixtures("mock_docker_app_context")
def test_dockerize_args_path_arg_and_env(mock_tools, my_app, tmp_path):
    """A command to run in Docker with paths inside the bundle and Briefcase data
    directory are dockerized."""
    dockerize_args = mock_tools[my_app].app_context._dockerize_args(
        ["hello", tmp_path / "location"],
        env={
            "MAGIC": "True",
            "PATH": (
                "/somewhere/safe"
                f":{tmp_path / 'briefcase' / 'tools'}"
                f":{tmp_path / 'bundle' / 'location'}"
            ),
        },
        cwd=tmp_path / "cwd",
    )

    assert dockerize_args == {
        "args": [
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
        "env": {"DOCKER_CLI_HINTS": "false"},
    }
