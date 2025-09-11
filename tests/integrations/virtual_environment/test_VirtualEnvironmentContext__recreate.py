from unittest.mock import MagicMock

from briefcase.integrations.virtual_environment import VenvContext


def test_recreate_when_venv_exists(self, dummy_tools, venv_path):
    """Test recreate removes existing venv and creates new one."""

    context = VenvContext(dummy_tools, venv_path)
    context.exists = MagicMock(return_value=True)
    context.create = MagicMock()

    venv_path.mkdir()
    (venv_path / "pyvenv.cfg").touch()

    assert venv_path.exists()

    context.recreate()
    context.exists.assert_called_once()
    context.create.assert_called_once()

    assert not venv_path.exists()


def test_recreate_when_venv_missing(self, dummy_tools, venv_path):
    """Test recreate skips removal and creates new venv."""

    context = VenvContext(dummy_tools, venv_path)
    context.exists = MagicMock(return_value=False)
    context.create = MagicMock()

    assert not venv_path.exists()

    context.recreate()
    context.exists.assert_called_once()
    context.create.assert_called_once()

    assert not venv_path.exists()
