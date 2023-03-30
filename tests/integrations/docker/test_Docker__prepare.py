import subprocess
from unittest.mock import MagicMock

import pytest

from briefcase.exceptions import BriefcaseCommandError
from briefcase.integrations.base import ToolCache
from briefcase.integrations.docker import Docker
from briefcase.integrations.subprocess import Subprocess


@pytest.fixture
def mock_tools(mock_tools) -> ToolCache:
    mock_tools.subprocess = MagicMock(spec_set=Subprocess)
    mock_tools.docker = Docker(mock_tools)
    return mock_tools


def test_prepare(mock_tools):
    """A docker image can be prepared"""

    # Prepare an image
    mock_tools.docker.prepare("ubuntu:jammy")

    mock_tools.subprocess.run.assert_called_once_with(
        ["docker", "run", "--rm", "ubuntu:jammy", "printf", ""],
        check=True,
        stream_output=False,
    )


def test_prepare_bad_image(mock_tools):
    """If an image is invalid, an exception raised,"""
    # Mock a Docker failure due to a bad image
    mock_tools.subprocess.run.side_effect = subprocess.CalledProcessError(
        returncode=125,
        cmd="docker...",
    )

    # Try to prepare an image that doesn't exist:
    with pytest.raises(
        BriefcaseCommandError,
        match=r"Unable to obtain the Docker base image ubuntu:does-not-exist.",
    ):
        mock_tools.docker.prepare("ubuntu:does-not-exist")

    # The subprocess call was made.
    mock_tools.subprocess.run.assert_called_once_with(
        ["docker", "run", "--rm", "ubuntu:does-not-exist", "printf", ""],
        check=True,
        stream_output=False,
    )
