import subprocess
from pathlib import PurePosixPath
from unittest.mock import MagicMock, call

import pytest

import briefcase
from briefcase.config import AppConfig
from briefcase.integrations.base import ToolCache
from briefcase.integrations.docker import DockerAppContext


@pytest.fixture
def mock_tools(mock_tools, tmp_path) -> ToolCache:
    # Mock stdlib subprocess module
    mock_tools.subprocess._subprocess = MagicMock(spec_set=subprocess)

    # Reset `os` mock without `spec` so tests can run on Windows where os.getuid doesn't exist.
    mock_tools.os = MagicMock()
    # Mock user and group IDs for docker image
    mock_tools.os.getuid.return_value = "37"
    mock_tools.os.getgid.return_value = "42"

    # Mock return values for run
    run_result = MagicMock(spec=subprocess.CompletedProcess, returncode=3)
    mock_tools.subprocess._subprocess.run.return_value = run_result

    # Mock return values for check_output
    mock_tools.subprocess._subprocess.check_output.return_value = "goodbye\n"

    # Short circuit the process streamer
    wait_bar_streamer = MagicMock()
    wait_bar_streamer.stdout.readline.return_value = ""
    wait_bar_streamer.poll.return_value = 0
    mock_tools.subprocess._subprocess.Popen.return_value.__enter__.return_value = (
        wait_bar_streamer
    )

    return mock_tools


@pytest.fixture
def my_app() -> AppConfig:
    return AppConfig(
        app_name="myapp",
        formal_name="My App",
        bundle="com.example",
        version="1.2.3",
        description="This is a simple app",
        sources=["path/to/src/myapp", "other/stuff"],
        system_requires=["things==1.2", "stuff>=3.4"],
    )


@pytest.fixture
def mock_docker_app_context(tmp_path, my_app, mock_tools) -> DockerAppContext:
    mock_docker_app_context = DockerAppContext(mock_tools, my_app)
    mock_docker_app_context.prepare(
        image_tag="briefcase/com.example.myapp:py3.X",
        dockerfile_path=tmp_path / "bundle" / "Dockerfile",
        app_base_path=tmp_path / "base",
        host_bundle_path=tmp_path / "bundle",
        host_data_path=tmp_path / "briefcase",
        python_version="3.X",
    )

    # Reset the mock so that the prepare call doesn't appear in test results.
    mock_docker_app_context.tools.subprocess._subprocess.Popen.reset_mock()

    return mock_docker_app_context


@pytest.fixture
def user_mapping_run_calls(tmp_path, monkeypatch) -> list:
    # Mock the container write test path in to pytest's tmp directory
    monkeypatch.setattr(
        briefcase.integrations.docker.Docker,
        "_write_test_path",
        MagicMock(return_value=tmp_path / "build" / "mock_write_test"),
    )
    return [
        call(
            [
                "docker",
                "run",
                "--rm",
                "--volume",
                f"{tmp_path / 'build'}:/host_write_test:z",
                "alpine",
                "touch",
                PurePosixPath("/host_write_test/mock_write_test"),
            ],
            check=True,
        ),
        call(
            [
                "docker",
                "run",
                "--rm",
                "--volume",
                f"{tmp_path / 'build'}:/host_write_test:z",
                "alpine",
                "rm",
                "-f",
                PurePosixPath("/host_write_test/mock_write_test"),
            ],
            check=True,
        ),
    ]
