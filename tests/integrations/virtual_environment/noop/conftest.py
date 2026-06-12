import pytest

from briefcase.integrations.virtual_environment import NoOpVirtualEnvironment


@pytest.fixture
def venv(mock_tools, venv_path):
    return NoOpVirtualEnvironment(mock_tools, venv_path)
