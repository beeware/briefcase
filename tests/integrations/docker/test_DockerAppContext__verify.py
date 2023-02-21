import subprocess
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from briefcase.exceptions import BriefcaseCommandError
from briefcase.integrations.docker import DockerAppContext
from briefcase.integrations.subprocess import Subprocess


@pytest.fixture
def verify_kwargs():
    return dict(
        image_tag="com.example.first-app:py3.X",
        dockerfile_path=Path("/path/to/Dockerfile"),
        app_base_path=Path("/app/base"),
        host_platform_path=Path("/host/platform"),
        host_data_path=Path("/host/data"),
        python_version="py3.X",
    )


def test_short_circuit(mock_tools, first_app_config, verify_kwargs):
    """Tool is not created if already cached."""
    mock_tools[first_app_config].app_context = "tool"

    app_context = DockerAppContext.verify(mock_tools, first_app_config, **verify_kwargs)

    assert app_context == "tool"
    assert app_context == mock_tools[first_app_config].app_context


def test_success(mock_tools, first_app_config, verify_kwargs):
    """Docker app context is successfully created and prepared."""
    mock_tools.subprocess = MagicMock(spec_set=Subprocess)
    # Mock the existence of Docker.
    mock_tools.subprocess.check_output.side_effect = [
        "Docker version 19.03.8, build afacb8b\n",
        "docker info return value",
    ]

    DockerAppContext.verify(mock_tools, first_app_config, **verify_kwargs)

    assert isinstance(mock_tools[first_app_config].app_context, DockerAppContext)

    # Docker image is created/updated
    mock_tools.subprocess.run.assert_called_with(
        [
            "docker",
            "build",
            "--progress",
            "plain",
            "--tag",
            "com.example.first-app:py3.X",
            "--file",
            Path("/path/to/Dockerfile"),
            "--build-arg",
            "PY_VERSION=py3.X",
            "--build-arg",
            "SYSTEM_REQUIRES=",
            "--build-arg",
            "HOST_UID=37",
            "--build-arg",
            "HOST_GID=42",
            Path("/app/base/src"),
        ],
        check=True,
    )


def test_docker_verify_fail(mock_tools, first_app_config, verify_kwargs):
    """Failure if Docker cannot be verified."""
    mock_tools.subprocess = MagicMock(spec_set=Subprocess)
    # Mock the existence of Docker.
    mock_tools.subprocess.check_output.side_effect = FileNotFoundError

    with pytest.raises(BriefcaseCommandError, match="Briefcase requires Docker"):
        DockerAppContext.verify(mock_tools, first_app_config, **verify_kwargs)


def test_docker_image_build_fail(mock_tools, first_app_config, verify_kwargs):
    """Failure if Docker image build fails."""
    mock_tools.subprocess = MagicMock(spec_set=Subprocess)
    # Mock the existence of Docker.
    mock_tools.subprocess.check_output.side_effect = [
        "Docker version 19.03.8, build afacb8b\n",
        "docker info return value",
    ]

    mock_tools.subprocess.run.side_effect = subprocess.CalledProcessError(
        returncode=80, cmd=["docker" "build"]
    )

    with pytest.raises(
        BriefcaseCommandError,
        match="Error building Docker container image for first-app",
    ):
        DockerAppContext.verify(mock_tools, first_app_config, **verify_kwargs)
