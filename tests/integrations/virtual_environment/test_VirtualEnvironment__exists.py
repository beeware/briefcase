from unittest.mock import MagicMock

import pytest

from briefcase.integrations.virtual_environment import VirtualEnvironment


@pytest.mark.parametrize("exists", [True, False])
def test_exists(mock_tools, exists):
    """Calls to exists() defer to the manager."""
    manager = MagicMock()
    manager.exists = MagicMock(return_value=exists)
    env = VirtualEnvironment(mock_tools, manager, recreate=False)

    assert env.exists() == exists
