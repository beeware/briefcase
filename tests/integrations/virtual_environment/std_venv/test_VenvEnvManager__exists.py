from briefcase.integrations.virtual_environment import VenvEnvManager


def test_exists_when_venv_and_config_exist(mock_tools, venv_path):
    """A venv exists when both the directory and pyvenv.cfg are present."""
    venv_path.mkdir()
    (venv_path / "pyvenv.cfg").touch()
    manager = VenvEnvManager(mock_tools, venv_path)
    assert manager.exists() is True


def test_does_not_exist_when_venv_path_missing(mock_tools, tmp_path):
    """A venv does not exist when the directory is missing."""
    venv = tmp_path / "nonexistent_venv"
    manager = VenvEnvManager(mock_tools, venv)
    assert manager.exists() is False


def test_does_not_exist_when_pyvenv_cfg_missing(mock_tools, venv_path):
    """A venv does not exist when the directory exists but pyvenv.cfg is missing."""
    venv_path.mkdir()
    manager = VenvEnvManager(mock_tools, venv_path)
    assert manager.exists() is False
