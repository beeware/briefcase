import pytest

from briefcase.integrations.virtual_environment import CondaVirtualEnvironment


@pytest.fixture
def venv(first_app, mock_tools, base_path):
    return CondaVirtualEnvironment(
        name="myenv",
        app=first_app,
        tools=mock_tools,
        base_path=base_path,
    )
