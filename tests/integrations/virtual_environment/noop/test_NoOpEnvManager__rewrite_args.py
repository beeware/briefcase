import pytest

from briefcase.integrations.virtual_environment import NoOpEnvManager


@pytest.fixture
def manager(mock_tools, venv_path):
    return NoOpEnvManager(mock_tools, venv_path)


@pytest.mark.parametrize("args", [[], ["python", "-m", "pip", "install", "package"]])
def test_rewrite_args(manager, args):
    """`rewrite_args` returns the args unmodified."""
    assert args is manager.rewrite_args(args)
