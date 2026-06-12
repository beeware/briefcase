import sys
from pathlib import Path


def test_executable_is_sys_executable(venv):
    """The `executable` is the active `sys.executable`."""
    assert venv.executable == Path(sys.executable)
    assert isinstance(venv.executable, Path)


def test_bin_dir_is_sys_executable_parent(venv):
    """The `bin_dir` is the directory containing `sys.executable`."""
    assert venv.bin_dir == Path(sys.executable).parent
    assert isinstance(venv.bin_dir, Path)
