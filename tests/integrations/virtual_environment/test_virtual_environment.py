import pytest

from briefcase.exceptions import BriefcaseCommandError
from briefcase.integrations.virtual_environment import (
    NoOpEnvironment,
    VenvEnvironment,
    virtual_environment,
)


def test_isolated_true_returns_venv_environment(mock_tools, dummy_console, venv_path):
    """Factory returns VenvEnvironment when isolated is true."""
    env = virtual_environment(mock_tools, dummy_console, venv_path, isolated=True)
    assert isinstance(env, VenvEnvironment)
    assert env.venv_path == venv_path


def test_isolated_false_returns_noop_environment(mock_tools, dummy_console, venv_path):
    """Factory returns NoOpEnvironment when isolated is false."""
    env = virtual_environment(mock_tools, dummy_console, venv_path, isolated=False)
    assert isinstance(env, NoOpEnvironment)


def test_isolated_default_true(mock_tools, dummy_console, venv_path):
    """Factory defaults to isolated=True."""
    env = virtual_environment(mock_tools, dummy_console, venv_path)
    assert isinstance(env, VenvEnvironment)


def test_recreate_default_false(mock_tools, dummy_console, venv_path):
    """Factory defaults to recreate=False."""
    env = virtual_environment(mock_tools, dummy_console, venv_path)
    assert isinstance(env, VenvEnvironment)
    assert env.recreate is False


def test_isolated_true_none_venv_path_raises_error(mock_tools, dummy_console):
    """Factory raises error when isolated=True but venv_path is None."""
    with pytest.raises(
        BriefcaseCommandError,
        match="A virtual environment path must be provided",
    ):
        virtual_environment(mock_tools, dummy_console, None, isolated=True)


def test_isolated_false_uses_marker_path(mock_tools, dummy_console, venv_path):
    """Factory creates marker path from venv_path when isolated is false."""
    env = virtual_environment(mock_tools, dummy_console, venv_path, isolated=False)

    assert isinstance(env, NoOpEnvironment)
    expected_marker = venv_path / "venv_path"
    assert env.noop_context.marker_path == expected_marker


def test_recreate_true_passes_to_venv_environment(mock_tools, dummy_console, venv_path):
    """Factory passes recreate=True to VenvEnvironment."""
    env = virtual_environment(mock_tools, dummy_console, venv_path, recreate=True)
    assert isinstance(env, VenvEnvironment)
    assert env.recreate is True


def test_venv_environment_receives_correct_parameters(
    mock_tools,
    dummy_console,
    venv_path,
):
    """VenvEnvironment receives all expected parameters from factory."""
    env = virtual_environment(
        mock_tools,
        dummy_console,
        venv_path,
        isolated=True,
        recreate=True,
    )

    assert isinstance(env, VenvEnvironment)
    assert env.tools == mock_tools
    assert env.console == dummy_console
    assert env.venv_path == venv_path
    assert env.recreate is True


def test_noop_environment_receives_correct_parameters(
    mock_tools,
    dummy_console,
    venv_path,
):
    """NoOpEnvironment receives all expected parameters from factory."""
    env = virtual_environment(
        mock_tools,
        dummy_console,
        venv_path,
        isolated=False,
    )

    assert isinstance(env, NoOpEnvironment)
    assert env.tools == mock_tools
    assert env.console == dummy_console
    assert env.noop_context.marker_path == venv_path / "venv_path"


def test_factory_with_explicit_false_recreate(mock_tools, dummy_console, venv_path):
    """Factory correctly handles explicit recreate=False."""
    env = virtual_environment(
        mock_tools,
        dummy_console,
        venv_path,
        isolated=True,
        recreate=False,
    )

    assert isinstance(env, VenvEnvironment)
    assert env.recreate is False
