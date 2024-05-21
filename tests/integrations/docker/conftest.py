from __future__ import annotations

import subprocess
from unittest.mock import MagicMock, call

import pytest

import briefcase
from briefcase.config import AppConfig
from briefcase.integrations.base import ToolCache
from briefcase.integrations.docker import Docker, DockerAppContext


@pytest.fixture
def mock_tools(mock_tools, tmp_path) -> ToolCache:
    # Mock stdlib subprocess module
    mock_tools.subprocess._subprocess = MagicMock(spec_set=subprocess)

    # Reset `os` mock without `spec` so tests can run on Windows where os.getuid doesn't exist.
    mock_tools.os = MagicMock()
    # Mock user and group IDs for docker image
    mock_tools.os.getuid.return_value = "37"
    mock_tools.os.getgid.return_value = "42"

    # Mock return values for run()
    run_result = MagicMock(spec=subprocess.CompletedProcess, returncode=3)
    mock_tools.subprocess._subprocess.run.return_value = run_result

    # Mock return values for check_output()
    mock_tools.subprocess._subprocess.check_output.return_value = "goodbye\n"

    # Mock the return value for Popen()
    popen_process = MagicMock(spec_set=subprocess.Popen)
    mock_tools.subprocess._subprocess.Popen = MagicMock(return_value=popen_process)
    # preserve the Popen process for test assertions
    mock_tools._popen_process = popen_process

    # Mock the Wait Bar streamer
    wait_bar_streamer = MagicMock()
    wait_bar_streamer.stdout.readline.return_value = ""
    wait_bar_streamer.poll.return_value = 0
    # assume using the Popen process in a context manager is for Wait Bar
    popen_process.__enter__.return_value = wait_bar_streamer

    return mock_tools


@pytest.fixture
def my_app() -> AppConfig:
    return AppConfig(
        app_name="myapp",
        formal_name="My App",
        bundle="com.example",
        version="1.2.3",
        description="This is a simple app",
        license={"file": "LICENSE"},
        sources=["path/to/src/myapp", "other/stuff"],
        system_requires=["things==1.2", "stuff>=3.4"],
        system_runtime_requires=["runtime_things==1.42", "stuff>=3.4"],
    )


@pytest.fixture
def mock_docker(mock_tools, monkeypatch) -> Docker:
    """Adds a mocked Docker to the mock_tools."""
    # Default to mapped users to avoid subprocess calls
    monkeypatch.setattr(
        Docker, "_is_user_mapping_enabled", MagicMock(return_value=True)
    )

    mock_tools.docker = Docker(mock_tools)

    mock_tools.os.environ = {"PROCESS_ENV_VAR": "VALUE"}

    # Reset the mock so that the user mapping calls don't appear in test results
    mock_tools.subprocess._subprocess.check_output.reset_mock()

    # Reset the LRU cache for Docker.cache_image() for each test
    Docker.cache_image.cache_clear()

    return mock_tools.docker


@pytest.fixture
def mock_docker_app_context(mock_tools, my_app, tmp_path) -> DockerAppContext:
    """Adds a mocked DockerAppContext to the mock_tools."""
    mock_tools[my_app].app_context = DockerAppContext(mock_tools, my_app)
    mock_tools[my_app].app_context.prepare(
        image_tag="briefcase/com.example.myapp:py3.X",
        dockerfile_path=tmp_path / "bundle/Dockerfile",
        app_base_path=tmp_path / "base",
        host_bundle_path=tmp_path / "bundle",
        host_data_path=tmp_path / "briefcase",
        python_version="3.X",
    )

    # Allow for asserting _dockerize_args() calls but still run logic
    mock_tools[my_app].app_context._dockerize_args = MagicMock(
        wraps=mock_tools[my_app].app_context._dockerize_args
    )

    # Reset the mock so that the prepare call doesn't appear in test results
    mock_tools[my_app].app_context.tools.subprocess._subprocess.Popen.reset_mock()

    return mock_tools[my_app].app_context


@pytest.fixture
def user_mapping_run_calls(tmp_path, monkeypatch) -> list[call]:
    """The series of calls for determining how users are mapped."""
    monkeypatch.setattr(
        briefcase.integrations.docker.Docker,
        "_write_test_path",
        MagicMock(return_value=tmp_path / "build/mock_write_test"),
    )
    return [
        call(
            ["docker", "images", "-q", "alpine"],
            env={"DOCKER_CLI_HINTS": "false"},
        ),
        call(
            args=[
                "docker",
                "run",
                "--rm",
                "--volume",
                f"{tmp_path / 'build'}:/host_write_test:z",
                "alpine",
                "touch",
                "/host_write_test/mock_write_test",
            ],
            env={"DOCKER_CLI_HINTS": "false"},
        ),
        call(
            args=[
                "docker",
                "run",
                "--rm",
                "--volume",
                f"{tmp_path / 'build'}:/host_write_test:z",
                "alpine",
                "rm",
                "-f",
                "/host_write_test/mock_write_test",
            ],
            env={"DOCKER_CLI_HINTS": "false"},
        ),
    ]
