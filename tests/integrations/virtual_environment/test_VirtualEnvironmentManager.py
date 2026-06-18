import pytest

from briefcase.integrations.virtual_environment import (
    NoOpVirtualEnvironment,
    VenvVirtualEnvironment,
    VirtualEnvironmentManager,
)


@pytest.fixture
def virtual_environment(mock_tools):
    return VirtualEnvironmentManager.verify(mock_tools)


def test_create_isolated_uses_VenvVirtualEnvironment(virtual_environment, venv_path):
    """Create(isolated=True) wires up a VenvVirtualEnvironment."""
    venv_path.mkdir()
    (venv_path / "pyvenv.cfg").touch()
    env = virtual_environment(venv_path, isolated=True, recreate=False)
    assert isinstance(env, VenvVirtualEnvironment)
    assert env.venv_path == venv_path


def test_create_non_isolated_uses_NoOpVirtualEnvironment(
    virtual_environment,
    venv_path,
):
    """Create(isolated=False) wires up a NoOpVirtualEnvironment."""
    env = virtual_environment(venv_path, isolated=False, recreate=False)
    assert isinstance(env, NoOpVirtualEnvironment)
    assert env.venv_path == venv_path
