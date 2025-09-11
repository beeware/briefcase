from briefcase.integrations.virtual_environment import VenvContext



"""Tests for the VenvContext.exists method."""

# both exist
def test_exists_when_venv_and_config_exists(self, dummy_tools, venv_path):
    """Test exists returns True when both venv and pyvenv.cfg exist."""
    venv_path.mkdir()
    (venv_path / "pyvenv.cfg").touch()
    context = VenvContext(dummy_tools, venv_path)
    assert context.exists() is True

# venv path missing
def test_exists_when_venv_path_missing(self, dummy_tools, tmp_path):
    """Tests exists returns False when venv path is missing."""
    venv = tmp_path / "nonexistent_venv"
    context = VenvContext(dummy_tools, venv)
    assert context.exists() is False

# venv exists, but pyvenv.cfg is missing
def test_exists_when_pyvenv_cfg_missing(self, dummy_tools, venv_path):
    """Tests exists returns False when venv exists but pyvenv.cfg is missing."""
    venv_path.mkdir()
    context = VenvContext(dummy_tools, venv_path)
    assert context.exists() is False

# both missing
def test_exists_when_both_missing(self, dummy_tools, tmp_path):
    """Tests exists returns False when both venv and pyvenv.cfg are missing."""
    venv = tmp_path / "nonexistent_venv"
    context = VenvContext(dummy_tools, venv)
    assert context.exists() is False
