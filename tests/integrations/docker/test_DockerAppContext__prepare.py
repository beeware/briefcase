import os
import subprocess

import pytest

from briefcase.exceptions import BriefcaseCommandError
from briefcase.integrations.docker import DockerAppContext


@pytest.mark.parametrize("extra_args", [[], ["--option-one", "--option-two"]])
def test_prepare(mock_tools, my_app, extra_args, tmp_path, sub_stream_kw):
    """The Docker environment can be prepared."""
    mock_docker_app_context = DockerAppContext(mock_tools, my_app)
    mock_docker_app_context.prepare(
        image_tag="briefcase/com.example.myapp:py3.X",
        dockerfile_path=tmp_path / "bundle/Dockerfile",
        app_base_path=tmp_path / "base",
        host_bundle_path=tmp_path / "bundle",
        host_data_path=tmp_path / "briefcase",
        python_version="3.X",
        extra_build_args=extra_args,
    )

    mock_docker_app_context.tools.subprocess._subprocess.Popen.assert_called_with(
        [
            "docker",
            "buildx",
            "build",
            "--load",
            "--progress",
            "plain",
            "--tag",
            "briefcase/com.example.myapp:py3.X",
            "--file",
            os.fsdecode(tmp_path / "bundle/Dockerfile"),
            "--build-arg",
            "SYSTEM_REQUIRES=things==1.2 stuff>=3.4 runtime_things==1.42 stuff>=3.4",
            "--build-arg",
            "HOST_UID=37",
            "--build-arg",
            "HOST_GID=42",
            os.fsdecode(tmp_path / "base/path/to/src"),
            *extra_args,
        ],
        **sub_stream_kw,
    )

    assert mock_docker_app_context.app_base_path == tmp_path / "base"
    assert mock_docker_app_context.host_bundle_path == tmp_path / "bundle"
    assert mock_docker_app_context.host_data_path == tmp_path / "briefcase"
    assert mock_docker_app_context.image_tag == "briefcase/com.example.myapp:py3.X"
    assert mock_docker_app_context.python_version == "3.X"


def test_prepare_failure(mock_docker_app_context, tmp_path, sub_stream_kw):
    """If the Docker environment can't be prepared, an error is raised."""
    # Mock a failure in docker build.
    mock_docker_app_context.tools.subprocess._subprocess.Popen.side_effect = (
        subprocess.CalledProcessError(returncode=1, cmd="docker build")
    )

    with pytest.raises(BriefcaseCommandError):
        mock_docker_app_context.prepare(
            image_tag="briefcase/com.example.myapp:py3.X",
            dockerfile_path=tmp_path / "bundle/Dockerfile",
            app_base_path=tmp_path / "base",
            host_bundle_path=tmp_path / "bundle",
            host_data_path=tmp_path / "briefcase",
            python_version="3.X",
            extra_build_args=["--option-one", "--option-two"],
        )

    mock_docker_app_context.tools.subprocess._subprocess.Popen.assert_called_with(
        [
            "docker",
            "buildx",
            "build",
            "--load",
            "--progress",
            "plain",
            "--tag",
            "briefcase/com.example.myapp:py3.X",
            "--file",
            os.fsdecode(tmp_path / "bundle/Dockerfile"),
            "--build-arg",
            "SYSTEM_REQUIRES=things==1.2 stuff>=3.4 runtime_things==1.42 stuff>=3.4",
            "--build-arg",
            "HOST_UID=37",
            "--build-arg",
            "HOST_GID=42",
            os.fsdecode(tmp_path / "base/path/to/src"),
            "--option-one",
            "--option-two",
        ],
        **sub_stream_kw,
    )
