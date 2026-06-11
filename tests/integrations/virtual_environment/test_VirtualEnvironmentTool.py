import pytest

from briefcase.integrations.virtual_environment import (
    NoOpEnvManager,
    VenvEnvManager,
    VirtualEnvironment,
    VirtualEnvironmentTool,
)


@pytest.fixture
def virtual_environment(mock_tools):
    return VirtualEnvironmentTool.verify(mock_tools)


@pytest.mark.parametrize("isolated", [True, False])
@pytest.mark.parametrize("recreate", [True, False])
def test_create_always_returns_VirtualEnvironment(
    virtual_environment,
    venv_path,
    isolated,
    recreate,
):
    """Create() returns a VirtualEnvironment for every input combination."""
    env = virtual_environment.create(venv_path, isolated=isolated, recreate=recreate)
    assert isinstance(env, VirtualEnvironment)


def test_create_isolated_uses_VenvEnvManager(virtual_environment, venv_path):
    """Create(isolated=True) wires up a VenvEnvManager."""
    venv_path.mkdir()
    (venv_path / "pyvenv.cfg").touch()
    env = virtual_environment.create(venv_path, isolated=True, recreate=False)
    assert isinstance(env.manager, VenvEnvManager)
    assert env.manager.venv_path == venv_path


def test_create_non_isolated_uses_NoOpEnvManager(virtual_environment, venv_path):
    """Create(isolated=False) wires up a NoOpEnvManager."""
    env = virtual_environment.create(venv_path, isolated=False, recreate=False)
    assert isinstance(env.manager, NoOpEnvManager)
    assert env.manager.venv_path == venv_path
