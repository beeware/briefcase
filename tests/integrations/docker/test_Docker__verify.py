import subprocess
from unittest.mock import MagicMock, call

import pytest

from briefcase.exceptions import BriefcaseCommandError
from briefcase.integrations.base import ToolCache
from briefcase.integrations.docker import Docker
from briefcase.integrations.subprocess import Subprocess


@pytest.fixture
def valid_docker_version():
    return "Docker version 19.03.8, build afacb8b\n"


@pytest.fixture
def mock_tools(mock_tools) -> ToolCache:
    mock_tools.subprocess = MagicMock(spec_set=Subprocess)
    return mock_tools


def test_short_circuit(mock_tools):
    """Tool is not created if already cached."""
    mock_tools.docker = "tool"

    tool = Docker.verify(mock_tools)

    assert tool == "tool"
    assert tool == mock_tools.docker


@pytest.mark.parametrize("host_os", ["Windows", "Linux", "Darwin"])
def test_docker_install_details(host_os):
    """Docker details available for each OS."""
    assert "install_url" in Docker.DOCKER_INSTALL_DETAILS[host_os]
    assert "extra_content" in Docker.DOCKER_INSTALL_DETAILS[host_os]


def test_docker_exists(mock_tools, valid_docker_version, capsys):
    """If docker exists, the Docker wrapper is returned."""
    # Mock the return value of Docker Version
    mock_tools.subprocess.check_output.side_effect = [
        valid_docker_version,
        "docker info return value",
    ]

    # Invoke docker verify
    result = Docker.verify(mock_tools)

    # The verify call should return the Docker wrapper
    assert isinstance(result, Docker)

    mock_tools.subprocess.check_output.assert_has_calls(
        [
            call(
                ["docker", "--version"],
                stderr=subprocess.STDOUT,
            ),
            call(
                ["docker", "info"],
                stderr=subprocess.STDOUT,
            ),
        ]
    )

    # No console output
    output = capsys.readouterr()
    assert output.out == ""
    assert output.err == ""


def test_docker_doesnt_exist(mock_tools):
    """If docker doesn't exist, an error is raised."""
    # Mock the return value of Docker Version
    mock_tools.subprocess.check_output.side_effect = FileNotFoundError

    # Invoke Docker verify
    with pytest.raises(BriefcaseCommandError):
        Docker.verify(mock_tools)

    # But docker was invoked
    mock_tools.subprocess.check_output.assert_called_with(
        ["docker", "--version"],
        stderr=subprocess.STDOUT,
    )


def test_docker_failure(mock_tools, capsys):
    """If docker failed during execution, the Docker wrapper is returned with a
    warning."""
    # Mock the return value of Docker Version
    mock_tools.subprocess.check_output.side_effect = [
        subprocess.CalledProcessError(
            returncode=1,
            cmd="docker --version",
        ),
        "Success!",
    ]

    # Invoke Docker verify
    result = Docker.verify(mock_tools)

    # The verify call should return the Docker wrapper
    assert isinstance(result, Docker)

    mock_tools.subprocess.check_output.assert_has_calls(
        [
            call(
                ["docker", "--version"],
                stderr=subprocess.STDOUT,
            ),
            call(
                ["docker", "info"],
                stderr=subprocess.STDOUT,
            ),
        ]
    )

    # console output
    output = capsys.readouterr()
    assert "** WARNING: Unable to determine if Docker is installed" in output.out
    assert output.err == ""


def test_docker_bad_version(mock_tools, capsys):
    """If docker exists but the version string doesn't make sense, the Docker
    wrapper is returned with a warning."""
    # Mock a bad return value of `docker --version`
    mock_tools.subprocess.check_output.return_value = "Docker version 17.2\n"

    # Invoke Docker verify
    with pytest.raises(
        BriefcaseCommandError, match=r"Briefcase requires Docker 19 or higher"
    ):
        Docker.verify(mock_tools)


def test_docker_unknown_version(mock_tools, capsys):
    """If docker exists but the version string doesn't make sense, the Docker
    wrapper is returned with a warning."""
    # Mock a bad return value of `docker --version`
    mock_tools.subprocess.check_output.return_value = "ceci nest pas un Docker\n"

    # Invoke Docker verify
    result = Docker.verify(mock_tools)

    # The verify call should return the Docker wrapper
    assert isinstance(result, Docker)

    mock_tools.subprocess.check_output.assert_has_calls(
        [
            call(
                ["docker", "--version"],
                stderr=subprocess.STDOUT,
            ),
            call(
                ["docker", "info"],
                stderr=subprocess.STDOUT,
            ),
        ]
    )

    # console output
    output = capsys.readouterr()
    assert "** WARNING: Unable to determine the version of Docker" in output.out
    assert output.err == ""


def test_docker_exists_but_process_lacks_permission_to_use_it(
    mock_tools,
    valid_docker_version,
):
    """If the docker daemon isn't running, the check fails."""
    message1 = """
Client:
 Debug Mode: false

Server:
ERROR: Got permission denied while trying to connect to the Docker daemon socket at unix:///var/run/docker.sock: """

    message2 = """Get http://%2Fvar%2Frun%2Fdocker.sock/v1.40/info: dial unix /var/run/docker.sock: connect: permission denied
errors pretty printing info"""  # noqa: E501

    error_message = message1 + message2
    # splitting it up is to appease flake8 line length - not sure how to add noqa to a triple quoted string line

    mock_tools.subprocess.check_output.side_effect = [
        valid_docker_version,
        subprocess.CalledProcessError(
            returncode=1,
            cmd="docker info",
            output=error_message,
        ),
    ]
    with pytest.raises(BriefcaseCommandError) as exc_info:
        Docker.verify(mock_tools)

    assert "does not have\npermissions to invoke Docker." in exc_info.value.msg


docker_not_running_error_messages = [
    """
    Client:
     Debug Mode: false

    Server:
    ERROR: Error response from daemon: dial unix docker.raw.sock: connect: connection refused
    errors pretty printing info
    """,  # this is the error shown on mac
    """
    Client:
     Debug Mode: false

    Server:
    ERROR: Cannot connect to the Docker daemon at unix:///var/run/docker.sock. Is the docker daemon running?
    errors pretty printing info""",  # this is the error show on linux
]


@pytest.mark.parametrize("error_message", docker_not_running_error_messages)
def test_docker_exists_but_is_not_running(
    error_message,
    mock_tools,
    valid_docker_version,
):
    """If the docker daemon isn't running, the check fails."""
    mock_tools.subprocess.check_output.side_effect = [
        valid_docker_version,
        subprocess.CalledProcessError(
            returncode=1,
            cmd="docker info",
            output=error_message,
        ),
    ]
    with pytest.raises(BriefcaseCommandError) as exc_info:
        Docker.verify(mock_tools)

    assert "the Docker\ndaemon is not running" in exc_info.value.msg


def test_docker_exists_but_unknown_error_when_running_command(
    mock_tools,
    valid_docker_version,
):
    """If docker info fails in unknown ways, the check fails."""
    mock_tools.subprocess.check_output.side_effect = [
        valid_docker_version,
        subprocess.CalledProcessError(
            returncode=1,
            cmd="docker info",
            output="This command failed!",
        ),
    ]

    with pytest.raises(BriefcaseCommandError) as exc_info:
        Docker.verify(mock_tools)

    assert "Check your Docker\ninstallation, and try again" in exc_info.value.msg
