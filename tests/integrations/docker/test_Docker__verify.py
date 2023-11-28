import subprocess
from collections import namedtuple
from pathlib import Path, PurePosixPath
from unittest.mock import MagicMock, call

import pytest

from briefcase.exceptions import BriefcaseCommandError, UnsupportedHostError
from briefcase.integrations.base import ToolCache
from briefcase.integrations.docker import Docker
from briefcase.integrations.subprocess import Subprocess

VALID_DOCKER_VERSION = "Docker version 19.03.8, build afacb8b\n"
VALID_DOCKER_INFO = "docker info printout"
VALID_BUILDX_VERSION = "github.com/docker/buildx v0.10.2 00ed17d\n"
VALID_USER_MAPPING_IMAGE_CACHE = "1ed313b0551f"
DOCKER_VERIFICATION_CALLS = [
    call(["docker", "--version"]),
    call(["docker", "info"]),
    call(["docker", "buildx", "version"]),
]


@pytest.fixture
def mock_tools(mock_tools) -> ToolCache:
    mock_tools.subprocess = MagicMock(spec_set=Subprocess)
    return mock_tools


@pytest.fixture
def mock_write_test_path(tmp_path, monkeypatch):
    """Mock the container write test path in to pytest's tmp directory."""
    write_test_path = tmp_path / "mock_write_test"
    # Wrap the path so read-only methods can be replaced
    write_test_path = MagicMock(wraps=write_test_path)
    monkeypatch.setattr(Docker, "_write_test_path", lambda self: write_test_path)
    return write_test_path


def test_short_circuit(mock_tools):
    """Tool is not created if already cached."""
    mock_tools.docker = "tool"

    tool = Docker.verify(mock_tools)

    assert tool == "tool"
    assert tool == mock_tools.docker


def test_unsupported_os(mock_tools):
    """When host OS is not supported, an error is raised."""
    mock_tools.host_os = "wonky"

    with pytest.raises(
        UnsupportedHostError,
        match=f"{Docker.name} is not supported on wonky",
    ):
        Docker.verify(mock_tools)


@pytest.mark.parametrize("host_os", ["Windows", "Linux", "Darwin"])
def test_docker_install_url(host_os):
    """Docker details available for each OS."""
    assert host_os in Docker.DOCKER_INSTALL_URL


def test_docker_exists(mock_tools, user_mapping_run_calls, capsys, tmp_path):
    """If docker exists, the Docker wrapper is returned."""
    # Mock the return value of Docker Version
    mock_tools.subprocess.check_output.side_effect = [
        VALID_DOCKER_VERSION,
        VALID_DOCKER_INFO,
        VALID_BUILDX_VERSION,
        VALID_USER_MAPPING_IMAGE_CACHE,
    ]

    # Invoke docker verify
    result = Docker.verify(mock_tools)

    # The verify call should return the Docker wrapper
    assert isinstance(result, Docker)

    # Docker version and plugins were verified
    mock_tools.subprocess.check_output.assert_has_calls(DOCKER_VERIFICATION_CALLS)

    # Docker user mapping inspection occurred
    mock_tools.subprocess.run.assert_has_calls(user_mapping_run_calls)

    # No console output
    output = capsys.readouterr()
    assert output.out == ""
    assert output.err == ""


def test_docker_doesnt_exist(mock_tools):
    """If docker doesn't exist, an error is raised."""
    # Mock Docker not installed on system
    mock_tools.subprocess.check_output.side_effect = FileNotFoundError

    # Invoke Docker verify
    with pytest.raises(BriefcaseCommandError):
        Docker.verify(mock_tools)

    # But docker was invoked
    mock_tools.subprocess.check_output.assert_called_with(["docker", "--version"])


def test_docker_failure(mock_tools, user_mapping_run_calls, capsys):
    """If docker failed during execution, the Docker wrapper is returned with a
    warning."""
    # Mock Docker cannot be found
    mock_tools.subprocess.check_output.side_effect = [
        subprocess.CalledProcessError(
            returncode=1,
            cmd="docker --version",
        ),
        "Success!",
        VALID_BUILDX_VERSION,
        VALID_USER_MAPPING_IMAGE_CACHE,
    ]

    # Invoke Docker verify
    result = Docker.verify(mock_tools)

    # The verify call should return the Docker wrapper
    assert isinstance(result, Docker)

    # Docker version and plugins were verified
    mock_tools.subprocess.check_output.assert_has_calls(DOCKER_VERIFICATION_CALLS)

    # Docker user mapping inspection occurred
    mock_tools.subprocess.run.assert_has_calls(user_mapping_run_calls)

    # console output
    output = capsys.readouterr()
    assert "** WARNING: Unable to determine if Docker is installed" in output.out
    assert output.err == ""


def test_docker_bad_version(mock_tools, capsys):
    """If docker exists but the version string doesn't make sense, the Docker wrapper is
    returned with a warning."""
    # Mock a bad return value of `docker --version`
    mock_tools.subprocess.check_output.return_value = "Docker version 17.2\n"

    # Invoke Docker verify
    with pytest.raises(
        BriefcaseCommandError,
        match=r"Briefcase requires Docker 19 or higher",
    ):
        Docker.verify(mock_tools)


def test_docker_unknown_version(mock_tools, user_mapping_run_calls, capsys):
    """If docker exists but the version string doesn't make sense, the Docker wrapper is
    returned with a warning."""
    # Mock a bad return value of `docker --version`
    mock_tools.subprocess.check_output.return_value = "ceci nest pas un Docker\n"

    # Invoke Docker verify
    result = Docker.verify(mock_tools)

    # The verify call should return the Docker wrapper
    assert isinstance(result, Docker)

    # Docker version and plugins were verified
    mock_tools.subprocess.check_output.assert_has_calls(DOCKER_VERIFICATION_CALLS)

    # Docker user mapping inspection occurred
    mock_tools.subprocess.run.assert_has_calls(user_mapping_run_calls)

    # console output
    output = capsys.readouterr()
    assert "** WARNING: Unable to determine the version of Docker" in output.out
    assert output.err == ""


def test_docker_exists_but_process_lacks_permission_to_use_it(mock_tools):
    """If the docker daemon isn't running, the check fails."""
    error_message = """
Client:
 Debug Mode: false

Server:
ERROR: Got permission denied while trying to connect to the Docker daemon socket at unix:///var/run/docker.sock:

Get http://%2Fvar%2Frun%2Fdocker.sock/v1.40/info: dial unix /var/run/docker.sock: connect: permission denied
errors pretty printing info"""

    mock_tools.subprocess.check_output.side_effect = [
        VALID_DOCKER_VERSION,
        subprocess.CalledProcessError(
            returncode=1,
            cmd="docker info",
            output=error_message,
        ),
    ]
    with pytest.raises(
        BriefcaseCommandError,
        match="does not have\npermissions to invoke Docker.",
    ):
        Docker.verify(mock_tools)


@pytest.mark.parametrize(
    "error_message",
    [
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
    ],
)
def test_docker_exists_but_is_not_running(error_message, mock_tools):
    """If the docker daemon isn't running, the check fails."""
    mock_tools.subprocess.check_output.side_effect = [
        VALID_DOCKER_VERSION,
        subprocess.CalledProcessError(
            returncode=1,
            cmd="docker info",
            output=error_message,
        ),
    ]
    with pytest.raises(
        BriefcaseCommandError,
        match="the Docker\ndaemon is not running",
    ):
        Docker.verify(mock_tools)


def test_docker_exists_but_unknown_error_when_running_command(mock_tools):
    """If docker info fails in unknown ways, the check fails."""
    mock_tools.subprocess.check_output.side_effect = [
        VALID_DOCKER_VERSION,
        subprocess.CalledProcessError(
            returncode=1,
            cmd="docker info",
            output="This command failed!",
        ),
    ]

    with pytest.raises(
        BriefcaseCommandError,
        match="Check your Docker\ninstallation, and try again",
    ):
        Docker.verify(mock_tools)


def test_buildx_plugin_not_installed(mock_tools):
    """If the buildx plugin is not installed, verification fails."""
    mock_tools.subprocess.check_output.side_effect = [
        VALID_DOCKER_VERSION,
        VALID_DOCKER_INFO,
        subprocess.CalledProcessError(
            returncode=1,
            cmd="docker buildx version",
        ),
    ]

    with pytest.raises(
        BriefcaseCommandError,
        match="Docker is installed and available for use but the buildx plugin\nis not installed",
    ):
        Docker.verify(mock_tools)


def test_docker_image_hint(mock_tools):
    """If an image_tag is passed to verification, it is used for the user mapping
    check."""
    # Mock the return values for Docker verification
    mock_tools.subprocess.check_output.side_effect = [
        VALID_DOCKER_VERSION,
        VALID_DOCKER_INFO,
        VALID_BUILDX_VERSION,
        VALID_USER_MAPPING_IMAGE_CACHE,
    ]

    Docker.verify(mock_tools, image_tag="myimage:tagtorulethemall")

    mock_tools.subprocess.run.assert_has_calls(
        [
            call(
                [
                    "docker",
                    "run",
                    "--rm",
                    "--volume",
                    f"{Path.cwd() / 'build'}:/host_write_test:z",
                    "myimage:tagtorulethemall",
                    "touch",
                    PurePosixPath("/host_write_test/container_write_test"),
                ],
                check=True,
            ),
            call(
                [
                    "docker",
                    "run",
                    "--rm",
                    "--volume",
                    f"{Path.cwd() / 'build'}:/host_write_test:z",
                    "myimage:tagtorulethemall",
                    "rm",
                    "-f",
                    PurePosixPath("/host_write_test/container_write_test"),
                ],
                check=True,
            ),
        ]
    )


def test_user_mapping_write_file_path(mock_tools):
    """The write test file path is as expected."""
    expected_path = Path.cwd() / "build/container_write_test"
    assert Docker(mock_tools)._write_test_path() == expected_path


def test_user_mapping_write_file_exists(mock_tools, mock_write_test_path):
    """Docker verification fails when the container write test file exists and cannot be
    deleted."""
    # Mock the return values for Docker verification
    mock_tools.subprocess.check_output.side_effect = [
        VALID_DOCKER_VERSION,
        VALID_DOCKER_INFO,
        VALID_BUILDX_VERSION,
        VALID_USER_MAPPING_IMAGE_CACHE,
    ]

    # Mock failure for deleting an existing write test file
    mock_write_test_path.unlink = MagicMock(side_effect=OSError("delete failed"))

    # Fails when file cannot be deleted
    with pytest.raises(
        BriefcaseCommandError,
        match="file path used to determine how Docker is mapping users",
    ):
        Docker.verify(mock_tools)


def test_user_mapping_write_test_file_creation_fails(mock_tools, mock_write_test_path):
    """Docker verification fails if the write test file cannot be written."""
    # Mock the return values for Docker verification
    mock_tools.subprocess.check_output.side_effect = [
        VALID_DOCKER_VERSION,
        VALID_DOCKER_INFO,
        VALID_BUILDX_VERSION,
        VALID_USER_MAPPING_IMAGE_CACHE,
    ]

    # Mock failure for deleting an existing write test file
    mock_tools.subprocess.run.side_effect = subprocess.CalledProcessError(
        returncode=1, cmd=["docker", "run", "..."]
    )

    # Fails when file cannot be deleted
    with pytest.raises(
        BriefcaseCommandError,
        match="Unable to determine if Docker is mapping users",
    ):
        Docker.verify(mock_tools)


def test_user_mapping_write_test_file_cleanup_fails(mock_tools, mock_write_test_path):
    """Docker verification fails if the write test file cannot be removed after the
    test."""
    # Mock the return values for Docker verification
    mock_tools.subprocess.check_output.side_effect = [
        VALID_DOCKER_VERSION,
        VALID_DOCKER_INFO,
        VALID_BUILDX_VERSION,
        VALID_USER_MAPPING_IMAGE_CACHE,
    ]

    # Mock failure for deleting an existing write test file
    mock_tools.subprocess.run.side_effect = [
        "container write test file creation succeeded",
        subprocess.CalledProcessError(returncode=1, cmd=["docker", "run", "..."]),
    ]

    # Fails when file cannot be deleted
    with pytest.raises(
        BriefcaseCommandError,
        match="Unable to clean up from determining if Docker is mapping users",
    ):
        Docker.verify(mock_tools)


@pytest.mark.parametrize("file_owner_id, expected", [(1000, True), (0, False)])
def test_user_mapping_setting(
    mock_tools,
    user_mapping_run_calls,
    file_owner_id,
    expected,
):
    """If the write test file is not owned by root, user mapping is enabled, else
    disabled."""
    # Mock the return values for Docker verification
    mock_tools.subprocess.check_output.side_effect = [
        VALID_DOCKER_VERSION,
        VALID_DOCKER_INFO,
        VALID_BUILDX_VERSION,
        VALID_USER_MAPPING_IMAGE_CACHE,
    ]

    stat_result = namedtuple("stat_result", "st_uid")
    # Mock the os.stat call returning a file owned by file_owner_id
    mock_tools.os.stat = MagicMock(return_value=stat_result(st_uid=file_owner_id))

    docker = Docker.verify(mock_tools)

    # Docker user mapping inspection occurred
    mock_tools.subprocess.run.assert_has_calls(user_mapping_run_calls)

    assert docker.is_user_mapped is expected
