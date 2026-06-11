import sys
from pathlib import Path

from briefcase.integrations.virtual_environment import NoOpEnvManager


def test_executable_is_sys_executable(mock_tools, venv_path):
    """The `executable` is active `sys.executable`."""
    manager = NoOpEnvManager(mock_tools, venv_path)
    assert manager.executable == Path(sys.executable)
    assert isinstance(manager.executable, Path)


def test_bin_dir_is_sys_executable_parent(mock_tools, venv_path):
    """The `bin_dir` is the directory containing `sys.executable`."""
    manager = NoOpEnvManager(mock_tools, venv_path)
    assert manager.bin_dir == Path(sys.executable).parent
    assert isinstance(manager.bin_dir, Path)
