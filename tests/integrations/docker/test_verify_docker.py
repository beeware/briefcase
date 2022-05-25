import subprocess
from unittest import mock

import pytest

from briefcase.console import Log
from briefcase.exceptions import BriefcaseCommandError
from briefcase.integrations.docker import Docker, _verify_docker_can_run, verify_docker


@pytest.fixture
def test_command(tmp_path):
    command = mock.MagicMock()
    command.logger = Log()

    return command


def test_docker_exists(test_command, capsys):
    """If docker exists, the Docker wrapper is returned."""
    # Mock the return value of Docker Version
    test_command.subprocess.check_output.return_value = (
        "Docker version 19.03.8, build afacb8b\n"
    )

    # Invoke verify_docker
    result = verify_docker(command=test_command)

    # The verify call should return the Docker wrapper
    assert result == Docker

    (
        docker_version_called_with,
        docker_info_called_with,
    ) = test_command.subprocess.check_output.call_args_list

    assert docker_version_called_with[0] == (["docker", "--version"],)
    assert docker_version_called_with[1] == {"stderr": subprocess.STDOUT}

    assert docker_info_called_with[0] == (["docker", "info"],)
    assert docker_info_called_with[1] == {"stderr": subprocess.STDOUT}

    # No console output
    output = capsys.readouterr()
    assert output.out == ""
    assert output.err == ""


def test_docker_doesnt_exist(test_command):
    """If docker doesn't exist, an error is raised."""
    # Mock the return value of Docker Version
    test_command.subprocess.check_output.side_effect = FileNotFoundError

    # Invoke verify_docker
    with pytest.raises(BriefcaseCommandError):
        verify_docker(command=test_command)

    # But docker was invoked
    test_command.subprocess.check_output.assert_called_with(
        ["docker", "--version"],
        stderr=subprocess.STDOUT,
    )


def test_docker_failure(test_command, capsys):
    """If docker failed during execution, the Docker wrapper is returned with a
    warning."""
    # Mock the return value of Docker Version
    test_command.subprocess.check_output.side_effect = [
        subprocess.CalledProcessError(
            returncode=1,
            cmd="docker --version",
        ),
        "Success!",
    ]

    # Invoke verify_docker
    result = verify_docker(command=test_command)

    # The verify call should return the Docker wrapper
    assert result == Docker

    (
        docker_version_called_with,
        docker_info_called_with,
    ) = test_command.subprocess.check_output.call_args_list

    assert docker_version_called_with[0] == (["docker", "--version"],)
    assert docker_version_called_with[1] == {"stderr": subprocess.STDOUT}

    assert docker_info_called_with[0] == (["docker", "info"],)
    assert docker_info_called_with[1] == {"stderr": subprocess.STDOUT}

    # console output
    output = capsys.readouterr()
    assert "** WARNING: Unable to determine if Docker is installed" in output.out
    assert output.err == ""


def test_docker_bad_version(test_command, capsys):
    """If docker exists but the version string doesn't make sense, the Docker
    wrapper is returned with a warning."""
    # Mock a bad return value of `docker --version`
    test_command.subprocess.check_output.return_value = "Docker version 17.2\n"

    # Invoke verify_docker
    with pytest.raises(
        BriefcaseCommandError, match=r"Briefcase requires Docker 19 or higher"
    ):
        verify_docker(command=test_command)


def test_docker_unknown_version(test_command, capsys):
    """If docker exists but the version string doesn't make sense, the Docker
    wrapper is returned with a warning."""
    # Mock a bad return value of `docker --version`
    test_command.subprocess.check_output.return_value = "ceci nest pas un Docker\n"

    # Invoke verify_docker
    result = verify_docker(command=test_command)

    # The verify call should return the Docker wrapper
    assert result == Docker

    (
        docker_version_called_with,
        docker_info_called_with,
    ) = test_command.subprocess.check_output.call_args_list

    assert docker_version_called_with[0] == (["docker", "--version"],)
    assert docker_version_called_with[1] == {"stderr": subprocess.STDOUT}

    assert docker_info_called_with[0] == (["docker", "info"],)
    assert docker_info_called_with[1] == {"stderr": subprocess.STDOUT}

    # console output
    output = capsys.readouterr()
    assert "** WARNING: Unable to determine the version of Docker" in output.out
    assert output.err == ""


def test_docker_exists_but_process_lacks_permission_to_use_it(test_command):
    """If the docker daemon isn't running, the check fails."""
    message1 = """
Client:
 Debug Mode: false

Server:
ERROR: Got permission denied while trying to connect to the Docker daemon socket at unix:///var/run/docker.sock: """

    message2 = """Get http://%2Fvar%2Frun%2Fdocker.sock/v1.40/info: dial unix /var/run/docker.sock: connect: permission denied
errors pretty printing info"""

    error_message = message1 + message2
    # splitting it up is to appease flake8 line length - not sure how to add noqa to a triple quoted string line

    test_command.subprocess.check_output.side_effect = subprocess.CalledProcessError(
        returncode=1, cmd="docker info", output=error_message
    )
    with pytest.raises(BriefcaseCommandError) as exc_info:
        _verify_docker_can_run(command=test_command)

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
def test_docker_exists_but_is_not_running(error_message, test_command):
    """If the docker daemon isn't running, the check fails."""
    test_command.subprocess.check_output.side_effect = subprocess.CalledProcessError(
        returncode=1,
        cmd="docker info",
        output=error_message,
    )
    with pytest.raises(BriefcaseCommandError) as exc_info:
        _verify_docker_can_run(command=test_command)

    assert "the Docker\ndaemon is not running" in exc_info.value.msg


def test_docker_exists_but_unknown_error_when_running_command(test_command):
    """If docker info fails in unknown ways, the check fails."""
    test_command.subprocess.check_output.side_effect = subprocess.CalledProcessError(
        returncode=1,
        cmd="docker info",
        output="This command failed!",
    )

    with pytest.raises(BriefcaseCommandError) as exc_info:
        _verify_docker_can_run(command=test_command)

    assert "Check your Docker\ninstallation, and try again" in exc_info.value.msg
