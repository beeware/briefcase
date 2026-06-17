import subprocess
import sys
from unittest.mock import MagicMock

import pytest

from briefcase.exceptions import BriefcaseCommandError
from briefcase.integrations.virtual_environment import CondaVirtualEnvironment

PYTHON_VERSION = f"{sys.version_info.major}.{sys.version_info.minor}"


@pytest.mark.parametrize("recreate", [True, False])
def test_create(mock_tools, venv_path, recreate):
    """A conda environment can be created."""
    venv = CondaVirtualEnvironment(mock_tools, venv_path, recreate=recreate)

    assert venv.created

    mock_tools.subprocess.run.assert_called_once_with(
        [
            "conda",
            "create",
            "--prefix",
            venv_path,
            f"python={PYTHON_VERSION}",
            "--yes",
            "--quiet",
        ],
        check=True,
    )


def test_creates_parent_directory(mock_tools, tmp_path):
    """Environment parent directories are created on demand."""
    venv_path = tmp_path / "nested" / "missing" / "test_venv"
    venv = CondaVirtualEnvironment(mock_tools, venv_path)

    assert venv.created
    assert venv_path.parent.is_dir()


def test_idempotent_when_venv_exists(mock_tools, venv_path):
    """If the environment already exists, creating the environment is a no-op."""
    venv_path.mkdir()
    (venv_path / "conda-meta").mkdir()

    venv = CondaVirtualEnvironment(mock_tools, venv_path)

    assert not venv.created
    mock_tools.subprocess.run.assert_not_called()


def test_recreate(mock_tools, venv_path):
    """If an environment already exists, recreating can be triggered."""
    venv_path.mkdir()
    (venv_path / "conda-meta").mkdir()

    venv = CondaVirtualEnvironment(mock_tools, venv_path, recreate=True)

    assert venv.created
    mock_tools.subprocess.run.assert_called_once_with(
        [
            "conda",
            "create",
            "--prefix",
            venv_path,
            f"python={PYTHON_VERSION}",
            "--yes",
            "--quiet",
        ],
        check=True,
    )


def test_venv_failure(mock_tools, venv_path):
    """If the environment can't be created, BriefcaseCommandError is raised."""
    mock_tools.subprocess.run = MagicMock(
        side_effect=subprocess.CalledProcessError(returncode=1, cmd="conda")
    )

    with pytest.raises(
        BriefcaseCommandError,
        match=r"Failed to create virtual environment at ",
    ):
        CondaVirtualEnvironment(mock_tools, venv_path)

    mock_tools.subprocess.run.assert_called_once_with(
        [
            "conda",
            "create",
            "--prefix",
            venv_path,
            f"python={PYTHON_VERSION}",
            "--yes",
            "--quiet",
        ],
        check=True,
    )
