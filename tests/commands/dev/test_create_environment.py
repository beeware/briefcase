import shutil
import subprocess
import sys

import pytest

from briefcase.exceptions import BriefcaseCommandError


def test_create_environment(dev_command, first_app):
    """Test that it creates a venv for the app."""
    venv_path = (
        dev_command.base_path / ".briefcase" / f"dev-web-venv-{first_app.app_name}"
    )

    # Ensure the environment path does not exist before the test so it can be created
    if venv_path.exists():
        shutil.rmtree(venv_path)
    assert not venv_path.exists()

    dev_command.create_environment(first_app)

    assert venv_path.exists()
    assert (venv_path / "pyvenv.cfg").exists()


def test_environment_exists(dev_command, first_app, capsys):
    """Test that the dev command does not create a venv for a specific app if one
    already exists."""
    venv_path = (
        dev_command.base_path / ".briefcase" / f"dev-web-venv-{first_app.app_name}"
    )
    venv_path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run([sys.executable, "-m", "venv", str(venv_path)], check=True)
    assert (venv_path / "pyvenv.cfg").exists()

    dev_command.create_environment(first_app)

    captured = capsys.readouterr()
    assert (
        f"Isolated virtual environment for {first_app.app_name} already exists. Skipping it's creation...."
        in captured.out
    )


def test_error_creating_environment(monkeypatch, dev_command, first_app):
    """Test that an error in creating the venv is handled gracefully."""
    venv_path = (
        dev_command.base_path / ".briefcase" / f"dev-web-venv-{first_app.app_name}"
    )

    # Ensure the environment path does not exist before the test so it can be created
    if venv_path.exists():
        shutil.rmtree(venv_path)
    assert not venv_path.exists()

    def mock_run(*args, **kwargs):
        raise subprocess.CalledProcessError(returncode=1, cmd=args[0])

    monkeypatch.setattr(subprocess, "run", mock_run)

    with pytest.raises(
        BriefcaseCommandError,
        match=f"Failed to create virtual environment for {first_app.app_name}.",
    ):
        dev_command.create_environment(first_app)
