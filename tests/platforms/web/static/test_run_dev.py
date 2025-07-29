import re
import shutil
import subprocess
import sys

import pytest

from briefcase.console import Console
from briefcase.exceptions import UnsupportedCommandError
from briefcase.platforms.web.static import StaticWebDevCommand


@pytest.fixture
def dev_command(tmp_path):
    return StaticWebDevCommand(
        console=Console(),
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )


def test_run_dev_app_creates_venv(dev_command, first_app_built):
    """Test that the dev command creates a virtual environment for the app."""
    venv_path = (
        dev_command.base_path
        / ".briefcase"
        / f"dev-web-venv-{first_app_built.app_name}"
    )
    if venv_path.exists():
        shutil.rmtree(venv_path)
    assert not venv_path.exists()

    with pytest.raises(
        UnsupportedCommandError,
        match=re.escape(
            "The Dev command for the  Web format has not been implemented (yet!)."
        ),
    ):
        dev_command.run_dev_app(first_app_built, env={})

    assert venv_path.exists()
    assert (venv_path / "pyvenv.cfg").exists()


def test_run_dev_app_existing_venv(dev_command, first_app_built, capsys):
    """Test that the dev command does not create a venv for a specific app if one
    already exists."""
    venv_path = (
        dev_command.base_path
        / ".briefcase"
        / f"dev-web-venv-{first_app_built.app_name}"
    )
    venv_path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run([sys.executable, "-m", "venv", str(venv_path)], check=True)
    assert (venv_path / "pyvenv.cfg").exists()

    with pytest.raises(
        UnsupportedCommandError,
        match=re.escape(
            "The Dev command for the  Web format has not been implemented (yet!)."
        ),
    ):
        dev_command.run_dev_app(first_app_built, env={})

    captured = capsys.readouterr()
    assert "Virtual environment for web development already exists." in captured.out


def test_run_dev_app_unsupported(dev_command, first_app_built):
    with pytest.raises(
        UnsupportedCommandError,
        match=re.escape(
            "The Dev command for the  Web format has not been implemented (yet!)."
        ),
    ):
        dev_command.run_dev_app(first_app_built, env={})
