import sys
from pathlib import Path

import pytest

from briefcase.integrations.virtual_environment import VenvEnvManager


@pytest.fixture
def manager(mock_tools, venv_path):
    return VenvEnvManager(mock_tools, venv_path)


@pytest.mark.parametrize(
    "empty_args",
    [
        [],
        (),
        None,
    ],
)
def test_rewrite_args_empty(manager, empty_args):
    """Empty inputs are returned unchanged."""
    result = manager.rewrite_args(empty_args)
    assert result == empty_args


@pytest.mark.parametrize(
    ("args", "expected_suffix"),
    [
        ([sys.executable], []),
        (
            [sys.executable, "-m", "pip", "install", "package"],
            ["-m", "pip", "install", "package"],
        ),
        (
            [Path(sys.executable), "-c", "print('hello')"],
            ["-c", "print('hello')"],
        ),
    ],
)
def test_rewrite_args_replaces_system_python(manager, args, expected_suffix):
    """The head argument is replaced when it equals sys.executable."""
    result = manager.rewrite_args(args)
    assert result == [manager.executable, *expected_suffix]


@pytest.mark.parametrize(
    "args",
    [
        ["/usr/bin/python3"],
        ["pip", "install", "package"],
        ("python", "-c", "import sys"),
    ],
)
def test_rewrite_args_no_replacement(manager, args):
    """Arguments whose head is not sys.executable are converted to a list verbatim."""
    result = manager.rewrite_args(args)
    assert result == list(args)
    assert isinstance(result, list)


@pytest.mark.skipif(sys.platform != "win32", reason="Windows specific test")
def test_rewrite_args_case_insensitive(manager):
    """On Windows, `rewrite_args` is case-insensitive."""
    result = manager.rewrite_args([sys.executable.lower(), "-V"])
    assert result == [manager.executable, "-V"]
