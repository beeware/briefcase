import inspect
import os
import platform
import shutil
import subprocess
import sys
import time
from unittest.mock import ANY, MagicMock

import pytest

from briefcase.config import DraftAppConfig
from briefcase.integrations.base import ToolCache
from briefcase.integrations.file import File
from briefcase.integrations.subprocess import Subprocess
from briefcase.integrations.virtual_environment import VirtualEnvironment

from .utils import DummyConsole, create_file


def pytest_sessionstart(session):
    """Ensure that tests don't use a color console."""

    os.environ["TERM"] = "dumb"
    os.environ["NO_COLOR"] = "1"
    try:
        del os.environ["FORCE_COLOR"]
    except KeyError:
        pass


# alias so fixtures can still use them
_print = print
_sleep = time.sleep


def monkeypatched_print(*args, **kwargs):
    """Raise an error for calls to print() from briefcase."""
    frame = inspect.currentframe().f_back
    module = inspect.getmodule(frame.f_code)

    # Disallow any use of a bare print() in the briefcase codebase
    if module and module.__name__.startswith("briefcase."):
        pytest.fail(
            "print() should not be invoked directly. Use Log or Console for printing."
        )

    _print(*args, **kwargs)


@pytest.fixture
def dummy_console():
    console = DummyConsole()
    yield console
    console.close()


@pytest.fixture(autouse=True)
def no_print(monkeypatch):
    """Replace builtin ``print()`` for ALL tests."""
    monkeypatch.setattr("builtins.print", monkeypatched_print)


@pytest.fixture
def sleep_zero(monkeypatch):
    """Replace all calls to ``time.sleep(x)`` with ``time.sleep(0)``."""
    monkeypatch.setattr(time, "sleep", MagicMock(wraps=lambda x: _sleep(0)))


@pytest.fixture
def sub_kw():
    """Default keyword arguments for all subprocess calls."""
    return {
        "text": True,
        "encoding": ANY,
        "errors": "backslashreplace",
    }


@pytest.fixture
def sub_check_output_kw(sub_kw):
    """Default keyword arguments for all subprocess.check_output calls."""
    return {
        **sub_kw,
        "stderr": subprocess.STDOUT,
    }


@pytest.fixture
def sub_stream_kw(sub_kw):
    """Default keyword arguments for all output streaming subprocess calls."""
    return {
        **sub_kw,
        "stdout": subprocess.PIPE,
        "stderr": subprocess.STDOUT,
        "bufsize": 1,
    }


@pytest.fixture
def first_app_config(tmp_path):
    create_file(tmp_path / "base_path" / "LICENSE", "MIT License")
    return DraftAppConfig(
        app_name="first",
        bundle="com.example",
        version="0.0.1",
        description="The first simple app",
        sources=["src/first"],
        license="MIT",
        license_files=["LICENSE"],
    )


@pytest.fixture
def first_app_unbuilt(first_app_config, tmp_path):
    # The same fixture as first_app_config,
    # but ensures that the bundle for the app exists
    create_file(
        tmp_path
        / "base_path"
        / "build"
        / "first"
        / "tester"
        / "dummy"
        / "first.bundle",
        "first.bundle",
    )

    return first_app_config


@pytest.fixture
def first_app(first_app_unbuilt, tmp_path):
    # The same fixture as first_app_config,
    # but ensures that the binary for the app exists
    create_file(
        tmp_path / "base_path/build/first/tester/dummy/first.bin",
        "first.bin",
    )

    return first_app_unbuilt


@pytest.fixture
def base_venv_path(tmp_path):
    return tmp_path / "mock_venvs"


@pytest.fixture
def mock_tools(dummy_console, tmp_path) -> ToolCache:
    mock_tools = ToolCache(
        console=dummy_console,
        base_path=tmp_path / "tools",
        home_path=tmp_path / "home",
    )

    # Mock stdlib tools
    mock_tools.os = MagicMock(spec_set=os)
    mock_tools.platform = MagicMock(spec_set=platform)
    mock_tools.shutil = MagicMock(spec_set=shutil)
    mock_tools.sys = MagicMock(spec_set=sys)

    # Mock an empty environment
    mock_tools.os.environ = {}

    # Create base directories
    mock_tools.base_path.mkdir(parents=True)
    mock_tools.home_path.mkdir(parents=True)

    # Make File and Subprocess always available
    File.verify(tools=mock_tools)
    Subprocess.verify(tools=mock_tools)

    return mock_tools


@pytest.fixture
def mock_venv(mock_tools, base_venv_path):
    venv = MagicMock(spec=VirtualEnvironment)
    venv.provides_python = False
    venv.tools = mock_tools
    venv.name = "mock-venv"
    venv.base_path = base_venv_path
    venv.venv_path = base_venv_path / "mock-venv"

    # create the venv directory
    venv.venv_path.mkdir(parents=True)

    return venv
