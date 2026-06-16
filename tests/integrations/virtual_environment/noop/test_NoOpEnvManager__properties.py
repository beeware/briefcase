import sys
from pathlib import Path


def test_executable_is_sys_executable(noop_venv):
    """The `executable` is the active `sys.executable`."""
    assert noop_venv.executable == Path(sys.executable)
    assert isinstance(noop_venv.executable, Path)


def test_bin_dir_is_sys_executable_parent(noop_venv):
    """The `bin_dir` is the directory containing `sys.executable`."""
    assert noop_venv.bin_dir == Path(sys.executable).parent
    assert isinstance(noop_venv.bin_dir, Path)
