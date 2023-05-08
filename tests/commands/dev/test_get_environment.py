import sys
from pathlib import Path

import pytest

PYTHONPATH = "PYTHONPATH"
PYTHONMALLOC = "PYTHONMALLOC"


@pytest.mark.skipif(sys.platform != "win32", reason="Relevant only for windows")
def test_pythonpath_with_one_source_in_windows(dev_command, first_app):
    """Test get environment with one source."""
    env = dev_command.get_environment(first_app, test_mode=False)
    assert env[PYTHONPATH] == f"{Path.cwd() / 'src'}"
    assert env[PYTHONMALLOC] == "default"


@pytest.mark.skipif(sys.platform != "win32", reason="Relevant only for windows")
def test_pythonpath_with_one_source_test_mode_in_windows(dev_command, first_app):
    """Test get environment with one source, no tests sources, in test mode."""
    env = dev_command.get_environment(first_app, test_mode=True)
    assert env[PYTHONPATH] == f"{Path.cwd() / 'src'}"
    assert env[PYTHONMALLOC] == "default"


@pytest.mark.skipif(sys.platform != "win32", reason="Relevant only for windows")
def test_pythonpath_with_two_sources_in_windows(dev_command, third_app):
    """Test get environment with two sources in windows."""
    env = dev_command.get_environment(third_app, test_mode=False)
    assert env[PYTHONPATH] == f"{Path.cwd() / 'src'};{Path.cwd()}"
    assert env[PYTHONMALLOC] == "default"


@pytest.mark.skipif(sys.platform != "win32", reason="Relevant only for windows")
def test_pythonpath_with_two_sources_and_tests_in_windows(dev_command, third_app):
    """Test get environment with two sources and test sources in windows."""
    third_app.test_sources = ["tests", "path/to/other"]
    env = dev_command.get_environment(third_app, test_mode=True)
    assert (
        env[PYTHONPATH]
        == f"{Path.cwd() / 'src'};{Path.cwd()};{Path.cwd() / 'path' / 'to'}"
    )
    assert env[PYTHONMALLOC] == "default"


@pytest.mark.skipif(sys.platform == "win32", reason="Relevant only for non-windows")
def test_pythonpath_with_one_source(dev_command, first_app):
    """Test get environment with one source."""
    env = dev_command.get_environment(first_app, test_mode=False)
    assert env[PYTHONPATH] == f"{Path.cwd() / 'src'}"
    assert PYTHONMALLOC not in env


@pytest.mark.skipif(sys.platform == "win32", reason="Relevant only for non-windows")
def test_pythonpath_with_one_source_test_mode(dev_command, first_app):
    """Test get environment with one source, no tests sources, in test mode."""
    env = dev_command.get_environment(first_app, test_mode=True)
    assert env[PYTHONPATH] == f"{Path.cwd() / 'src'}"
    assert PYTHONMALLOC not in env


@pytest.mark.skipif(sys.platform == "win32", reason="Relevant only for non-windows")
def test_pythonpath_with_two_sources_in_linux(dev_command, third_app):
    """Test get environment with two sources in linux."""
    env = dev_command.get_environment(third_app, test_mode=False)
    assert env[PYTHONPATH] == f"{Path.cwd() / 'src'}:{Path.cwd()}"
    assert PYTHONMALLOC not in env


@pytest.mark.skipif(sys.platform == "win32", reason="Relevant only for non-windows")
def test_pythonpath_with_two_sources_and_tests_in_linux(dev_command, third_app):
    """Test get environment with two sources and test sources in linux."""
    env = dev_command.get_environment(third_app, test_mode=True)
    assert (
        env[PYTHONPATH]
        == f"{Path.cwd() / 'src'}:{Path.cwd()}:{Path.cwd() / 'path' / 'to'}"
    )
    assert PYTHONMALLOC not in env
