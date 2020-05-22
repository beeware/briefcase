import subprocess

import pytest

from briefcase.exceptions import BriefcaseCommandError


def test_prepare(mock_docker, tmp_path):
    "The Docker environment can be prepared"

    mock_docker.prepare()

    mock_docker._subprocess._subprocess.run.assert_called_with(
        [
            'docker',
            'build',
            '--tag', 'briefcase/com.example.myapp:py3.X',
            '--file', str(tmp_path / 'bundle' / 'Dockerfile'),
            '--build-arg', "PY_VERSION=3.X",
            '--build-arg', "SYSTEM_REQUIRES=things==1.2 stuff>=3.4",
            '--build-arg', "HOST_UID=37",
            '--build-arg', "HOST_GID=42",
            str(tmp_path / "base" / "path" / "to" / "src")
        ],
        check=True,
    )


def test_prepare_failure(mock_docker, tmp_path):
    "If the Docker environment can't be prepared, an error is raised."
    # Mock a failure in docker build.
    mock_docker._subprocess._subprocess.run.side_effect = subprocess.CalledProcessError(
        returncode=1, cmd='docker build'
    )

    with pytest.raises(BriefcaseCommandError):
        mock_docker.prepare()

    mock_docker._subprocess._subprocess.run.assert_called_with(
        [
            'docker',
            'build',
            '--tag', 'briefcase/com.example.myapp:py3.X',
            '--file', str(tmp_path / 'bundle' / 'Dockerfile'),
            '--build-arg', "PY_VERSION=3.X",
            '--build-arg', "SYSTEM_REQUIRES=things==1.2 stuff>=3.4",
            '--build-arg', "HOST_UID=37",
            '--build-arg', "HOST_GID=42",
            str(tmp_path / "base" / "path" / "to" / "src")
        ],
        check=True,
    )
