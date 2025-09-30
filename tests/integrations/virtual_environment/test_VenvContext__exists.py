from briefcase.integrations.virtual_environment import VenvContext


def test_exists_when_venv_and_config_exists(mock_tools, venv_path):
    """A venv exists if both the directory and pyvenv.cfg file are present."""
    venv_path.mkdir()
    (venv_path / "pyvenv.cfg").touch()
    context = VenvContext(mock_tools, venv_path)
    assert context.exists() is True


def test_exists_when_venv_path_missing(mock_tools, tmp_path):
    """A venv does not exist if the directory is missing."""
    venv = tmp_path / "nonexistent_venv"
    context = VenvContext(mock_tools, venv)
    assert context.exists() is False


def test_exists_when_pyvenv_cfg_missing(mock_tools, venv_path):
    """A venv does not exist if the directory exists but pyvenv.cfg is missing."""
    venv_path.mkdir()
    context = VenvContext(mock_tools, venv_path)
    assert context.exists() is False
