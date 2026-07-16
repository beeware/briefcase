import pytest

from briefcase.integrations.virtual_environment import CondaVirtualEnvironment

pytest.skip(allow_module_level=True)


@pytest.fixture
def venv(mock_tools, venv_path):
    env = CondaVirtualEnvironment(mock_tools, venv_path)
    mock_tools.subprocess.run.reset_mock()
    return env
