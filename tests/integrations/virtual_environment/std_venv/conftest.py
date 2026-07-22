import pytest

from briefcase.integrations.virtual_environment import VenvVirtualEnvironment


@pytest.fixture
def venv(first_app, mock_tools, base_venv_path, tmp_path):
    return VenvVirtualEnvironment(
        name="myvenv",
        app=first_app,
        tools=mock_tools,
        base_path=base_venv_path,
    )
