import subprocess
from unittest.mock import MagicMock, call

import pytest

from briefcase.integrations.base import ToolCache
from briefcase.integrations.docker import Docker
from briefcase.integrations.subprocess import Subprocess


@pytest.fixture
def mock_tools(mock_tools) -> ToolCache:
    mock_tools.subprocess = MagicMock(spec_set=Subprocess)
    mock_tools.docker = Docker(mock_tools)
    return mock_tools


def test_check_output(mock_tools):
    """A command can be invoked on a bare Docker image."""
    # mock image already being cached in Docker
    mock_tools.subprocess.check_output.side_effect = ["1ed313b0551f", "output"]

    # Run the command in a container
    mock_tools.docker.check_output(["cmd", "arg1", "arg2"], image_tag="ubuntu:jammy")

    mock_tools.subprocess.check_output.assert_has_calls(
        [
            # Verify image is cached in Docker
            call(["docker", "images", "-q", "ubuntu:jammy"]),
            # Run command in Docker using image
            call(["docker", "run", "--rm", "ubuntu:jammy", "cmd", "arg1", "arg2"]),
        ]
    )


def test_check_output_fail(mock_tools):
    """Any subprocess errors are passed back through directly."""
    # mock image already being cached in Docker and check_output() call fails
    mock_tools.subprocess.check_output.side_effect = [
        "1ed313b0551f",
        subprocess.CalledProcessError(returncode=1, cmd=["cmd", "arg1", "arg2"]),
    ]

    # The CalledProcessError surfaces from Docker().check_output()
    with pytest.raises(subprocess.CalledProcessError):
        mock_tools.docker.check_output(
            ["cmd", "arg1", "arg2"], image_tag="ubuntu:jammy"
        )

    mock_tools.subprocess.check_output.assert_has_calls(
        [
            # Verify image is cached in Docker
            call(["docker", "images", "-q", "ubuntu:jammy"]),
            # Command errors in Docker using image
            call(["docker", "run", "--rm", "ubuntu:jammy", "cmd", "arg1", "arg2"]),
        ]
    )
