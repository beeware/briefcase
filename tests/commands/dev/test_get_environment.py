import sys
from pathlib import Path

import pytest

PYTHONPATH = "PYTHONPATH"


def test_pythonpath_with_one_source(dev_command, first_app):
    """Test get environment with one source."""
    env = dev_command.get_environment(first_app)
    assert env[PYTHONPATH] == f"{Path.cwd() / 'src'}"


@pytest.mark.skipif(sys.platform != "win32", reason="Relevant only for windows")
def test_pythonpath_with_two_sources_in_windows(dev_command, third_app):
    """Test get environment with two sources in windows."""
    env = dev_command.get_environment(third_app)
    assert env[PYTHONPATH] == f"{Path.cwd() / 'src'};{Path.cwd()}"


@pytest.mark.skipif(sys.platform == "win32", reason="Relevant only for non-windows")
def test_pythonpath_with_two_sources_in_linux(dev_command, third_app):
    """Test get environment with two sources in linux."""
    env = dev_command.get_environment(third_app)
    assert env[PYTHONPATH] == f"{Path.cwd() / 'src'}:{Path.cwd()}"
