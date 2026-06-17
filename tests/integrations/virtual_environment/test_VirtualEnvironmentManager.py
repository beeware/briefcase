import pytest

from briefcase.integrations.virtual_environment import (
    NoOpVirtualEnvironment,
    # CondaVirtualEnvironment,
    # PixiVirtualEnvironment,
    UvVirtualEnvironment,
    VenvVirtualEnvironment,
    VirtualEnvironmentManager,
)

ENV_MANAGERS = [
    ("venv", VenvVirtualEnvironment),
    ("uv", UvVirtualEnvironment),
    # ("conda", CondaVirtualEnvironment),
    # ("pixi", PixiVirtualEnvironment),
]


@pytest.fixture
def virtual_environment(mock_tools):
    return VirtualEnvironmentManager.verify(mock_tools)


@pytest.mark.parametrize(("env_manager", "manager_class"), ENV_MANAGERS)
def test_create_isolated_uses_VenvVirtualEnvironment(
    virtual_environment,
    venv_path,
    env_manager,
    manager_class,
):
    """Create(isolated=True) wires up a VenvVirtualEnvironment."""
    env = virtual_environment(
        venv_path,
        isolated=True,
        recreate=False,
        env_manager=env_manager,
    )
    assert isinstance(env, manager_class)
    assert env.venv_path == venv_path


@pytest.mark.parametrize(("env_manager", "manager_class"), ENV_MANAGERS)
def test_create_non_isolated_uses_NoOpVirtualEnvironment(
    virtual_environment,
    venv_path,
    env_manager,
    manager_class,
):
    """Create(isolated=False) *always* wires up a NoOpVirtualEnvironment."""
    env = virtual_environment(
        venv_path,
        isolated=False,
        recreate=False,
        env_manager=env_manager,
    )
    assert isinstance(env, NoOpVirtualEnvironment)
    assert env.venv_path == venv_path
