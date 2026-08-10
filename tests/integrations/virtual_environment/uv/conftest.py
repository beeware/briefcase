import pytest

from briefcase.integrations.virtual_environment import UvVirtualEnvironment


@pytest.fixture
def venv(first_app, mock_tools, base_path):
    return UvVirtualEnvironment(
        name="myenv",
        app=first_app,
        tools=mock_tools,
        base_path=base_path,
    )
