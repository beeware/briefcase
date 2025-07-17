import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from briefcase.exceptions import BriefcaseCommandError, UnsupportedHostError
from briefcase.integrations.docker import Docker, DockerAppContext


@pytest.fixture
def verify_kwargs():
    return {
        "image_tag": "com.example.first-app:py3.X",
        "dockerfile_path": Path("/path/to/Dockerfile"),
        "app_base_path": Path("/app/base"),
        "host_bundle_path": Path("/host/bundle"),
        "host_data_path": Path("/host/data"),
        "python_version": "py3.X",
        "extra_build_args": ["--option-one", "--option-two"],
    }


def test_short_circuit(mock_tools, first_app_config, verify_kwargs):
    """Tool is not created if already cached."""
    mock_tools[first_app_config].app_context = "tool"

    app_context = DockerAppContext.verify(mock_tools, first_app_config, **verify_kwargs)

    assert app_context == "tool"
    assert app_context == mock_tools[first_app_config].app_context


def test_unsupported_os(mock_tools, first_app_config, verify_kwargs):
    """When host OS is not supported, an error is raised."""
    mock_tools.host_os = "wonky"

    with pytest.raises(
        UnsupportedHostError,
        match=f"{DockerAppContext.name} is not supported on wonky",
    ):
        DockerAppContext.verify(mock_tools, first_app_config, **verify_kwargs)


@pytest.mark.skipif(
    sys.platform == "win32", reason="Windows paths aren't converted in Docker context"
)
@pytest.mark.usefixtures("mock_docker")
def test_success(mock_tools, first_app_config, verify_kwargs, sub_stream_kw):
    """Docker app context is successfully created and prepared."""

    DockerAppContext.verify(mock_tools, first_app_config, **verify_kwargs)

    assert isinstance(mock_tools[first_app_config].app_context, DockerAppContext)

    # Docker image is created/updated
    mock_tools.subprocess._subprocess.Popen.assert_called_with(
        [
            "docker",
            "buildx",
            "build",
            "--load",
            "--progress",
            "plain",
            "--tag",
            "com.example.first-app:py3.X",
            "--file",
            "/path/to/Dockerfile",
            "--build-arg",
            "SYSTEM_REQUIRES=",
            "--build-arg",
            "HOST_UID=37",
            "--build-arg",
            "HOST_GID=42",
            "/app/base/src",
            "--option-one",
            "--option-two",
        ],
        **sub_stream_kw,
    )


def test_docker_verify_fail(mock_tools, first_app_config, verify_kwargs, monkeypatch):
    """Failure if Docker cannot be verified."""
    monkeypatch.setattr(
        Docker,
        "verify_install",
        MagicMock(
            spec_set=Docker.verify_install,
            side_effect=BriefcaseCommandError("No docker for you"),
        ),
    )

    with pytest.raises(BriefcaseCommandError, match="No docker for you"):
        DockerAppContext.verify(mock_tools, first_app_config, **verify_kwargs)


@pytest.mark.usefixtures("mock_docker")
def test_docker_image_build_fail(mock_tools, first_app_config, verify_kwargs):
    """Failure if Docker image build fails."""
    mock_tools.subprocess._subprocess.Popen.side_effect = subprocess.CalledProcessError(
        returncode=80, cmd=["docker", "build"]
    )

    with pytest.raises(
        BriefcaseCommandError,
        match="Error building Docker container image for first-app",
    ):
        DockerAppContext.verify(mock_tools, first_app_config, **verify_kwargs)
