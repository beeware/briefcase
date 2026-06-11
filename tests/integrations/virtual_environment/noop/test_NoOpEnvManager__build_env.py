import pytest

from briefcase.integrations.virtual_environment import NoOpEnvManager


@pytest.fixture
def manager(mock_tools, venv_path):
    return NoOpEnvManager(mock_tools, venv_path)


@pytest.mark.parametrize("env", [None, {}, {"CUSTOM": "value", "PATH": "/x"}])
def test_build_env(manager, env):
    """The environment isn't modified."""
    assert manager.build_env(env) is env
