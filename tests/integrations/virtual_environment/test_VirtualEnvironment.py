import pytest

from briefcase.integrations.virtual_environment import (
    NoOpEnvironment,
    VenvEnvironment,
    VirtualEnvironment,
)


@pytest.fixture
def virtual_environment(mock_tools):
    return VirtualEnvironment.verify(mock_tools)


def test_isolated(virtual_environment, venv_path):
    """Factory returns VenvEnvironment when isolated is true."""
    env = virtual_environment.create(venv_path, isolated=True, recreate=False)

    assert isinstance(env, VenvEnvironment)
    assert env.path == venv_path
    assert not env.recreate


def test_non_isolated(virtual_environment, venv_path):
    """Factory returns NoOpEnvironment when isolated is false."""
    env = virtual_environment.create(venv_path, isolated=False, recreate=False)

    assert isinstance(env, NoOpEnvironment)
    assert env.path == venv_path
    assert not env.recreate


def test_recreate_isolated(virtual_environment, venv_path):
    """An isolated environment can be re-created."""
    env = virtual_environment.create(venv_path, isolated=True, recreate=True)

    assert isinstance(env, VenvEnvironment)
    assert env.path == venv_path
    assert env.recreate


def test_recreate_non_isolated(virtual_environment, venv_path):
    """An non-isolated environment can be re-created."""
    env = virtual_environment.create(venv_path, isolated=False, recreate=True)

    assert isinstance(env, NoOpEnvironment)
    assert env.path == venv_path
    assert env.recreate
