import subprocess
from unittest.mock import call

import pytest


@pytest.mark.usefixtures("mock_docker")
def test_check_output(mock_tools, sub_check_output_kw):
    """A command can be invoked on a bare Docker image."""
    # mock image already being cached in Docker
    mock_tools.subprocess._subprocess.check_output.side_effect = [
        "1ed313b0551f",
        "output",
    ]

    # Run the command in a container
    mock_tools.docker.check_output(["cmd", "arg1", "arg2"], image_tag="ubuntu:jammy")

    mock_tools.subprocess._subprocess.check_output.assert_has_calls(
        [
            # Verify image is cached in Docker
            call(
                ["docker", "images", "-q", "ubuntu:jammy"],
                env={"PROCESS_ENV_VAR": "VALUE", "DOCKER_CLI_HINTS": "false"},
                **sub_check_output_kw,
            ),
            # Run command in Docker using image
            call(
                ["docker", "run", "--rm", "ubuntu:jammy", "cmd", "arg1", "arg2"],
                env={"PROCESS_ENV_VAR": "VALUE", "DOCKER_CLI_HINTS": "false"},
                **sub_check_output_kw,
            ),
        ]
    )


@pytest.mark.usefixtures("mock_docker")
def test_check_output_fail(mock_tools, sub_check_output_kw):
    """Any subprocess errors are passed back through directly."""
    # mock image already being cached in Docker and check_output() call fails
    mock_tools.subprocess._subprocess.check_output.side_effect = [
        "1ed313b0551f",
        subprocess.CalledProcessError(returncode=1, cmd=["cmd", "arg1", "arg2"]),
    ]

    # The CalledProcessError surfaces from Docker().check_output()
    with pytest.raises(subprocess.CalledProcessError):
        mock_tools.docker.check_output(
            ["cmd", "arg1", "arg2"], image_tag="ubuntu:jammy"
        )

    mock_tools.subprocess._subprocess.check_output.assert_has_calls(
        [
            # Verify image is cached in Docker
            call(
                ["docker", "images", "-q", "ubuntu:jammy"],
                env={"PROCESS_ENV_VAR": "VALUE", "DOCKER_CLI_HINTS": "false"},
                **sub_check_output_kw,
            ),
            # Command errors in Docker using image
            call(
                ["docker", "run", "--rm", "ubuntu:jammy", "cmd", "arg1", "arg2"],
                env={"PROCESS_ENV_VAR": "VALUE", "DOCKER_CLI_HINTS": "false"},
                **sub_check_output_kw,
            ),
        ]
    )
