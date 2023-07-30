import subprocess
from unittest.mock import MagicMock, call

import pytest

from briefcase.exceptions import BriefcaseCommandError
from briefcase.integrations.base import ToolCache
from briefcase.integrations.docker import Docker
from briefcase.integrations.subprocess import Subprocess


@pytest.fixture
def mock_tools(mock_tools, user_mapping_run_calls) -> ToolCache:
    mock_tools.subprocess = MagicMock(spec_set=Subprocess)
    mock_tools.docker = Docker(mock_tools)
    return mock_tools


def test_cache_image(mock_tools, user_mapping_run_calls):
    """A Docker image can be cached."""
    # mock image not being cached in Docker
    mock_tools.subprocess.check_output.return_value = ""

    # Cache an image
    mock_tools.docker.cache_image("ubuntu:jammy")

    # Confirms that image is not available
    mock_tools.subprocess.check_output.assert_called_with(
        ["docker", "images", "-q", "ubuntu:jammy"]
    )

    # Image is pulled and cached
    mock_tools.subprocess.run.assert_has_calls(
        user_mapping_run_calls
        + [call(["docker", "pull", "ubuntu:jammy"], check=True, stream_output=False)]
    )


def test_cache_image_already_cached(mock_tools, user_mapping_run_calls):
    """A Docker image is not pulled if it is already cached."""
    # mock image already cached in Docker
    mock_tools.subprocess.check_output.return_value = "99284ca6cea0"

    # Cache an image
    mock_tools.docker.cache_image("ubuntu:jammy")

    # Confirms that image is not available
    mock_tools.subprocess.check_output.assert_called_with(
        ["docker", "images", "-q", "ubuntu:jammy"]
    )

    # Image is not pulled and cached
    mock_tools.subprocess.run.assert_has_calls(user_mapping_run_calls)


def test_cache_bad_image(mock_tools):
    """If an image is invalid, an exception raised."""
    # mock image not being cached in Docker
    mock_tools.subprocess.check_output.return_value = ""

    # Mock a Docker failure due to a bad image
    mock_tools.subprocess.run.side_effect = subprocess.CalledProcessError(
        returncode=125,
        cmd="docker...",
    )

    # Try to cache an image that doesn't exist:
    with pytest.raises(
        BriefcaseCommandError,
        match=r"Unable to obtain the Docker image for ubuntu:does-not-exist.",
    ):
        mock_tools.docker.cache_image("ubuntu:does-not-exist")
