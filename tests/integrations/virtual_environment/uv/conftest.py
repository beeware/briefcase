import pytest

from briefcase.integrations.virtual_environment import UvVirtualEnvironment


@pytest.fixture
def venv(mock_tools, venv_path):
    env = UvVirtualEnvironment(mock_tools, venv_path)
    mock_tools.subprocess.run.reset_mock()
    return env
