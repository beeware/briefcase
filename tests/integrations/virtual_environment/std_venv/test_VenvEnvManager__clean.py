from briefcase.integrations.virtual_environment import VenvEnvManager

from ....utils import create_file


def test_clean_removes_existing_venv(mock_tools, venv_path):
    """Clean removes the venv directory tree when it exists."""
    create_file(venv_path / "pyvenv.cfg", "VENV CONFIG")
    manager = VenvEnvManager(mock_tools, venv_path)

    assert manager.exists()

    manager.clean()

    assert not manager.exists()
    assert not venv_path.exists()


def test_clean_is_noop_when_missing(mock_tools, venv_path):
    """Clean is a no-op when the venv does not exist."""
    manager = VenvEnvManager(mock_tools, venv_path)

    assert not manager.exists()

    manager.clean()

    assert not manager.exists()
