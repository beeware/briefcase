import pytest

from briefcase.exceptions import BriefcaseCommandError
from briefcase.integrations.virtual_environment import (
    NoOpEnvironment,
    VenvEnvironment,
    virtual_environment,
)


def test_isolated_true_returns_venv_environment(dummy_tools, dummy_console, venv_path):
    """Factory returns VenvEnvironment when isolated is true."""
    env = virtual_environment(dummy_tools, dummy_console, venv_path, isolated=True)
    assert isinstance(env, VenvEnvironment)
    assert env.venv_path == venv_path


def test_isolated_false_returns_noop_environment(dummy_tools, dummy_console, venv_path):
    """Factory returns NoOpEnvironment when isolated is false."""
    env = virtual_environment(dummy_tools, dummy_console, venv_path, isolated=False)
    assert isinstance(env, NoOpEnvironment)


def test_isolated_default_true(dummy_tools, dummy_console, venv_path):
    """Factory defaults to isolated=True."""
    env = virtual_environment(dummy_tools, dummy_console, venv_path)
    assert isinstance(env, VenvEnvironment)


def test_recreate_default_false(dummy_tools, dummy_console, venv_path):
    """Factory defaults to recreate=False."""
    env = virtual_environment(dummy_tools, dummy_console, venv_path)
    assert isinstance(env, VenvEnvironment)
    assert env.recreate is False


def test_isolated_true_none_venv_path_raises_error(dummy_tools, dummy_console):
    """Factory raises error when isolated=True but venv_path is None."""
    with pytest.raises(
        BriefcaseCommandError,
        match="A virtual environment path must be provided",
    ):
        virtual_environment(dummy_tools, dummy_console, None, isolated=True)
