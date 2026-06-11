from unittest.mock import MagicMock

from briefcase.integrations.virtual_environment import VirtualEnvironment


def test_clean(mock_tools):
    """Calls to exists() defer to the manager."""
    manager = MagicMock()
    manager.clean = MagicMock()
    env = VirtualEnvironment(mock_tools, manager, recreate=False)

    env.clean()

    manager.clean.assert_called_once_with()
