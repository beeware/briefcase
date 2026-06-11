from unittest.mock import MagicMock

from briefcase.integrations.virtual_environment import VirtualEnvironment


def test_create(mock_tools, venv_path):
    """An environment can be created."""
    manager = MagicMock()
    manager.prepare = MagicMock(return_value=True)

    env = VirtualEnvironment(mock_tools, manager, recreate=False)

    manager.prepare.assert_called_once_with(recreate=False)
    assert env.manager == manager
    assert env.created is True


def test_recreate(mock_tools, venv_path):
    """An environment can be recreated."""
    manager = MagicMock()
    manager.prepare = MagicMock(return_value=True)

    env = VirtualEnvironment(mock_tools, manager, recreate=True)

    manager.prepare.assert_called_once_with(recreate=True)
    assert env.manager == manager
    assert env.created is True
