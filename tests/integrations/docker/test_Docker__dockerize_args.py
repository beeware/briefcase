import sys
from pathlib import Path, PurePosixPath

import pytest


@pytest.mark.usefixtures("mock_docker")
def test_dockerize_simple_call(mock_tools):
    """Simple Docker command is returned."""
    args = mock_tools.docker.dockerize_args(
        ["hello", "world"],
        image_tag="best-image",
    )

    assert args == {
        "args": ["docker", "run", "--rm", "best-image", "hello", "world"],
        "env": {"DOCKER_CLI_HINTS": "false"},
    }


@pytest.mark.usefixtures("mock_docker")
def test_dockerize_interactive(mock_tools):
    """Docker command includes interactive session."""
    args = mock_tools.docker.dockerize_args(
        ["hello", "world"],
        image_tag="best-image",
        interactive=True,
    )

    assert args == {
        "args": ["docker", "run", "--rm", "-it", "best-image", "hello", "world"],
        "env": {"DOCKER_CLI_HINTS": "false"},
    }


@pytest.mark.usefixtures("mock_docker")
def test_dockerize_mounts(mock_tools):
    """Docker command includes bind mounts."""
    args = mock_tools.docker.dockerize_args(
        ["hello", "world"],
        image_tag="best-image",
        mounts=[
            ("/source/path_one", "/target/path_one"),
            ("/source/path_two", "/target/path_two"),
        ],
    )

    assert args == {
        "args": [
            "docker",
            "run",
            "--rm",
            "--volume",
            "/source/path_one:/target/path_one:z",
            "--volume",
            "/source/path_two:/target/path_two:z",
            "best-image",
            "hello",
            "world",
        ],
        "env": {"DOCKER_CLI_HINTS": "false"},
    }


@pytest.mark.skipif(
    sys.platform == "win32", reason="Windows paths aren't converted in Docker context"
)
@pytest.mark.usefixtures("mock_docker")
@pytest.mark.parametrize("cwd", ["/my/cwd", Path("/my/cwd"), PurePosixPath("/my/cwd")])
def test_dockerize_cwd(mock_tools, cwd):
    """Docker command includes working directory."""
    args = mock_tools.docker.dockerize_args(
        ["hello", "world"],
        image_tag="best-image",
        cwd=cwd,
    )

    assert args == {
        "args": [
            "docker",
            "run",
            "--rm",
            "--workdir",
            "/my/cwd",
            "best-image",
            "hello",
            "world",
        ],
        "env": {"DOCKER_CLI_HINTS": "false"},
    }


@pytest.mark.skipif(
    sys.platform == "win32", reason="Windows paths aren't converted in Docker context"
)
@pytest.mark.usefixtures("mock_docker")
def test_dockerize_env(mock_tools):
    """Docker command includes environment variables."""
    args = mock_tools.docker.dockerize_args(
        ["hello", "world"],
        image_tag="best-image",
        env={
            "ENVVAR1": "value",
            "ENVVAR2": "value with space",
            "ENVVAR3": "/my/str/path",
            "ENVVAR4": Path("/my/path/path"),
            "ENVVAR5": PurePosixPath("/my/pure/path/path"),
        },
    )

    assert args == {
        "args": [
            "docker",
            "run",
            "--rm",
            "--env",
            "ENVVAR1=value",
            "--env",
            "ENVVAR2=value with space",
            "--env",
            "ENVVAR3=/my/str/path",
            "--env",
            "ENVVAR4=/my/path/path",
            "--env",
            "ENVVAR5=/my/pure/path/path",
            "best-image",
            "hello",
            "world",
        ],
        "env": {"DOCKER_CLI_HINTS": "false"},
    }


@pytest.mark.usefixtures("mock_docker")
def test_dockerize_add_hosts(mock_tools):
    """Docker command includes hosts to map."""
    args = mock_tools.docker.dockerize_args(
        ["hello", "world"],
        image_tag="best-image",
        add_hosts=[
            ("host1.local", "1.1.1.1"),
            ("host2.local", "1.1.1.2"),
            ("host3.local", "example.com"),
        ],
    )

    assert args == {
        "args": [
            "docker",
            "run",
            "--rm",
            "--add-host",
            "host1.local:1.1.1.1",
            "--add-host",
            "host2.local:1.1.1.2",
            "--add-host",
            "host3.local:example.com",
            "best-image",
            "hello",
            "world",
        ],
        "env": {"DOCKER_CLI_HINTS": "false"},
    }


DOCKERIZE_TEST_PARAMS = [
    (
        {
            "interactive": True,
            "mounts": [
                ("/source/path_one", "/target/path_one"),
                ("/source/path_two", "/target/path_two"),
            ],
            "cwd": "/my/cwd/inside",
            "env": {
                "ENVVAR1": "value",
                "ENVVAR2": "value with space",
                "ENVVAR3": "/my/str/path",
                "ENVVAR4": Path("/my/path/path"),
                "ENVVAR5": PurePosixPath("/my/pure/path/path"),
            },
            "add_hosts": [
                ("host1.local", "1.1.1.1"),
                ("host2.local", "1.1.1.2"),
                ("host3.local", "example.com"),
            ],
        },
        {
            "args": [
                "docker",
                "run",
                "--rm",
                "-it",
                "--volume",
                "/source/path_one:/target/path_one:z",
                "--volume",
                "/source/path_two:/target/path_two:z",
                "--env",
                "ENVVAR1=value",
                "--env",
                "ENVVAR2=value with space",
                "--env",
                "ENVVAR3=/my/str/path",
                "--env",
                "ENVVAR4=/my/path/path",
                "--env",
                "ENVVAR5=/my/pure/path/path",
                "--workdir",
                "/my/cwd/inside",
                "--add-host",
                "host1.local:1.1.1.1",
                "--add-host",
                "host2.local:1.1.1.2",
                "--add-host",
                "host3.local:example.com",
                "best-image",
                "hello",
                "world",
            ],
            "env": {"DOCKER_CLI_HINTS": "false"},
        },
    )
]


@pytest.mark.skipif(
    sys.platform == "win32", reason="Windows paths aren't converted in Docker context"
)
@pytest.mark.parametrize("in_kwargs, out_args_kwargs", DOCKERIZE_TEST_PARAMS)
@pytest.mark.usefixtures("mock_docker")
def test_dockerized_complex_call(mock_tools, in_kwargs, out_args_kwargs):
    """Docker command includes combination of options."""
    args = mock_tools.docker.dockerize_args(
        ["hello", "world"],
        image_tag="best-image",
        **in_kwargs,
    )

    assert args == out_args_kwargs
