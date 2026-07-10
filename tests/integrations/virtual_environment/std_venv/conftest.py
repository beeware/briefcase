import pytest

from briefcase.integrations.virtual_environment import VenvVirtualEnvironment


@pytest.fixture
def venv(mock_tools, venv_path):
    return VenvVirtualEnvironment(mock_tools, venv_path)
