from unittest.mock import MagicMock

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

    # Run the command in a container
    mock_tools.docker.check_output(["cmd", "arg1", "arg2"], image_tag="ubuntu:jammy")

    mock_tools.subprocess.check_output.assert_called_once_with(
        ["docker", "run", "--rm", "ubuntu:jammy", "cmd", "arg1", "arg2"]
    )
