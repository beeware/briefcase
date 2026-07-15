import subprocess
import sys
from unittest.mock import ANY, MagicMock, call

import pytest

from briefcase.exceptions import BriefcaseCommandError
from briefcase.integrations.virtual_environment import VenvVirtualEnvironment


@pytest.mark.parametrize("recreate", [True, False])
def test_create(mock_tools, venv_path, recreate):
    """A Python venv can be created."""
    venv = VenvVirtualEnvironment(mock_tools, venv_path, recreate=recreate)

    assert venv.created

    mock_tools.subprocess.run.mock_calls = [
        call(
            [sys.executable, "-m", "venv", venv_path],
            check=True,
        ),
        call(
            [
                venv.executable,
                "-u",
                "-X",
                "utf8",
                "-m",
                "pip",
                "install",
                "--upgrade",
                "-vv",
                "pip",
            ],
            check=True,
            encoding="UTF-8",
            env=ANY,
        ),
    ]


def test_creates_parent_directory(mock_tools, tmp_path):
    """Environment parent directories on demand."""
    venv_path = tmp_path / "nested" / "missing" / "test_venv"
    venv = VenvVirtualEnvironment(mock_tools, venv_path)

    assert venv.created
    assert venv_path.parent.is_dir()


def test_idempotent_when_venv_exists(mock_tools, venv_path):
    """If the environment already exists, creating the environment is a no-op."""
    venv_path.mkdir()
    (venv_path / "pyvenv.cfg").touch()

    venv = VenvVirtualEnvironment(mock_tools, venv_path)

    assert not venv.created
    mock_tools.subprocess.run.assert_not_called()


def test_recreate(mock_tools, venv_path):
    """If an environment already exists, recreating can be triggered."""
    venv_path.mkdir()
    (venv_path / "pyvenv.cfg").touch()

    venv = VenvVirtualEnvironment(mock_tools, venv_path, recreate=True)

    assert venv.created
    mock_tools.subprocess.run.mock_calls = [
        call(
            [sys.executable, "-m", "venv", venv_path],
            check=True,
        ),
        call(
            [
                venv.executable,
                "-u",
                "-X",
                "utf8",
                "-m",
                "pip",
                "install",
                "--upgrade",
                "-vv",
                "pip",
            ],
            check=True,
            encoding="UTF-8",
            env=ANY,
        ),
    ]


def test_venv_failure(mock_tools, venv_path):
    """If the environment can't be created, BriefcaseCommandError is raised."""
    mock_tools.subprocess.run = MagicMock(
        side_effect=subprocess.CalledProcessError(returncode=1, cmd="venv")
    )

    with pytest.raises(
        BriefcaseCommandError,
        match=r"Failed to create virtual environment at ",
    ):
        VenvVirtualEnvironment(mock_tools, venv_path)

    mock_tools.subprocess.run.assert_called_once_with(
        [sys.executable, "-m", "venv", venv_path],
        check=True,
    )


def test_pip_upgrade_failure(mock_tools, venv_path):
    """If pip can't be upgraded, a BriefcaseCommandError is raised."""
    # Second subprocess call fails
    mock_tools.subprocess.run = MagicMock(
        side_effect=[
            0,
            subprocess.CalledProcessError(returncode=1, cmd="venv"),
        ]
    )

    with pytest.raises(
        BriefcaseCommandError,
        match=r"Failed to update core tooling for ",
    ):
        VenvVirtualEnvironment(mock_tools, venv_path)

    mock_tools.subprocess.run.mock_calls = [
        call(
            [sys.executable, "-m", "venv", venv_path],
            check=True,
        ),
        call(
            [
                ANY,
                "-u",
                "-X",
                "utf8",
                "-m",
                "pip",
                "install",
                "--upgrade",
                "-vv",
                "pip",
            ],
            check=True,
            encoding="UTF-8",
            env=ANY,
        ),
    ]
