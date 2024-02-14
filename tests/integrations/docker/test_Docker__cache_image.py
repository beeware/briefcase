import subprocess
from unittest.mock import call

import pytest

from briefcase.exceptions import BriefcaseCommandError


@pytest.mark.usefixtures("mock_docker")
def test_cache_image(mock_tools, sub_kw, sub_check_output_kw):
    """A Docker image can be cached."""
    # mock image not being cached in Docker
    mock_tools.subprocess._subprocess.check_output.return_value = ""

    # Cache an image
    mock_tools.docker.cache_image("ubuntu:jammy")

    # Confirms that image is not available
    mock_tools.subprocess._subprocess.check_output.assert_called_with(
        ["docker", "images", "-q", "ubuntu:jammy"],
        env={"PROCESS_ENV_VAR": "VALUE", "DOCKER_CLI_HINTS": "false"},
        **sub_check_output_kw,
    )

    # Image is pulled and cached
    mock_tools.subprocess._subprocess.run.assert_has_calls(
        [
            call(
                ["docker", "pull", "ubuntu:jammy"],
                check=True,
                env={"PROCESS_ENV_VAR": "VALUE", "DOCKER_CLI_HINTS": "false"},
                **sub_kw,
            ),
        ]
    )


@pytest.mark.usefixtures("mock_docker")
def test_cache_image_already_cached(mock_tools, sub_check_output_kw):
    """A Docker image is not pulled if it is already cached."""
    # mock image already cached in Docker
    mock_tools.subprocess._subprocess.check_output.return_value = "99284ca6cea0"

    # Cache an image
    mock_tools.docker.cache_image("ubuntu:jammy")

    # Confirms that image is not available
    mock_tools.subprocess._subprocess.check_output.assert_called_with(
        ["docker", "images", "-q", "ubuntu:jammy"],
        env={"PROCESS_ENV_VAR": "VALUE", "DOCKER_CLI_HINTS": "false"},
        **sub_check_output_kw,
    )

    # Image is not pulled and cached
    mock_tools.subprocess._subprocess.run.assert_has_calls([])


@pytest.mark.usefixtures("mock_docker")
def test_cache_bad_image(mock_tools):
    """If an image is invalid, an exception raised."""
    # mock image not being cached in Docker
    mock_tools.subprocess._subprocess.check_output.return_value = ""

    # Mock a Docker failure due to a bad image
    mock_tools.subprocess._subprocess.run.side_effect = subprocess.CalledProcessError(
        returncode=125, cmd="docker..."
    )

    # Try to cache an image that doesn't exist
    with pytest.raises(
        BriefcaseCommandError,
        match=r"Unable to obtain the Docker image for ubuntu:does-not-exist.",
    ):
        mock_tools.docker.cache_image("ubuntu:does-not-exist")
