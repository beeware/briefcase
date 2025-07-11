import importlib
import locale
import os
import platform
import shutil
import sys
from pathlib import Path
from unittest.mock import MagicMock

import httpx
import pytest
from cookiecutter.main import cookiecutter

import briefcase.integrations
from briefcase.console import Console
from briefcase.integrations.base import ToolCache

from .test_tool_registry import integrations_modules, tools_for_module


def test_toolcache_typing():
    """Tool typing for ToolCache is correct."""
    # Tools that are intentionally not annotated in ToolCache.
    tools_unannotated = {"cookiecutter"}
    # Tool names to exclude from the dynamic annotation checks; they are manually checked.
    tool_names_skip_dynamic_check = {
        "app_context",  # Tested by the Docker module
        "git",  # An external API, not a Briefcase Tool
        "xcode_cli",  # Tested by the Xcode module
        "ETC_OS_RELEASE",  # A constant, not a tool
    }
    # Tool classes to exclude from dynamic annotation checks.
    tool_klasses_skip_dynamic_checks = {
        "Git",
        "DockerAppContext",
        "NativeAppContext",
        "LinuxDeployQtPlugin",
        "LinuxDeployGtkPlugin",
        "LinuxDeployURLPlugin",
        "LinuxDeployLocalFilePlugin",
    }

    # Ensure all modules containing Tools are exported in ``briefcase.integrations``.
    assert sorted(integrations_modules()) == sorted(briefcase.integrations.__all__)

    # Ensure defined Tool modules/classes are annotated in ToolCache.
    for tool_module_name in briefcase.integrations.__all__:
        if tool_module_name not in tools_unannotated:
            assert tool_module_name in ToolCache.__annotations__
        for tool_name in tools_for_module(tool_module_name):
            if tool_name not in tool_klasses_skip_dynamic_checks:
                assert tool_name in ToolCache.__annotations__.values()

    # Ensure annotated tools use valid Tool names.
    for tool_name, tool_klass_name in ToolCache.__annotations__.items():
        if tool_name not in tool_names_skip_dynamic_check:
            assert tool_name in briefcase.integrations.__all__
            assert tool_klass_name in tools_for_module(tool_name)
            tool_klass = getattr(
                importlib.import_module(f"briefcase.integrations.{tool_name}"),
                tool_klass_name,
            )
            assert tool_name == tool_klass.name

    # Manually check tools that aren't Tool classes or use special annotations.
    app_context_klasses = [
        briefcase.integrations.docker.DockerAppContext.__name__,
        briefcase.integrations.subprocess.Subprocess.__name__,
    ]
    app_context_annotated = ToolCache.__annotations__["app_context"].split(" | ")
    assert sorted(app_context_klasses) == sorted(app_context_annotated)

    assert ToolCache.__annotations__["git"] == "git_"
    assert ToolCache.__annotations__["xcode_cli"] == "XcodeCliTools"
    assert ToolCache.__annotations__["ETC_OS_RELEASE"] == "Path"


def test_third_party_tools_available():
    """Third party tools are available."""
    assert ToolCache.os is os
    assert ToolCache.platform is platform
    assert ToolCache.shutil is shutil
    assert ToolCache.sys is sys

    assert ToolCache.cookiecutter is cookiecutter
    assert ToolCache.httpx is httpx


def test_always_true(simple_tools, tmp_path):
    """Implicit boolean casts are always True."""
    assert simple_tools or False
    simple_tools["app-1"].app_context = "tool"
    assert simple_tools["app-1"] or False


def test_mapping_protocol(simple_tools):
    """ToolCache is a mapping."""
    simple_tools["app-1"].tool = "tool 1"
    simple_tools["app-2"].tool = "tool 2"

    assert list(simple_tools) == ["app-1", "app-2"]
    assert len(simple_tools) == 2
    assert simple_tools["app-1"].tool == "tool 1"
    assert simple_tools["app-2"].tool == "tool 2"


def test_host_arch_and_os(simple_tools):
    """Arch and OS represent host arch and OS."""
    assert simple_tools.host_arch == platform.machine()
    assert simple_tools.host_os == platform.system()


def test_base_path_is_path(simple_tools):
    """Base path is always a Path."""
    # The BaseCommand tests have much more extensive tests for this path.
    assert isinstance(simple_tools.base_path, Path)
    tools = ToolCache(
        console=Console(),
        base_path="/home/data",
    )
    assert isinstance(tools.base_path, Path)


def test_home_path_default(simple_tools):
    """Home path default is current user's home directory."""
    assert simple_tools.home_path == Path.home()


@pytest.mark.skipif(platform.system() == "Windows", reason="Linux/macOS specific tests")
@pytest.mark.parametrize(
    "home_path, expected_path",
    [
        (None, Path.home()),
        ("/path/to/home", Path("/path/to/home")),
        ("~", Path.home()),
        ("~/dir", Path.home() / "dir"),
    ],
)
def test_nonwindows_home_path(home_path, expected_path, tmp_path):
    """Home path is always expanded or defaulted."""
    tools = ToolCache(
        console=Console(),
        base_path=tmp_path,
        home_path=home_path,
    )
    assert tools.home_path == expected_path


@pytest.mark.skipif(platform.system() != "Windows", reason="Windows specific tests")
@pytest.mark.parametrize(
    "home_path, expected_path",
    [
        (None, Path.home()),
        ("Y:\\path\\to\\home", Path("Y:\\path\\to\\home")),
        ("~", Path.home()),
        ("~/dir", Path.home() / "dir"),
    ],
)
def test_windows_home_path(home_path, expected_path, tmp_path):
    """Home path is always expanded or defaulted."""
    tools = ToolCache(
        console=Console(),
        base_path=tmp_path,
        home_path=home_path,
    )
    assert tools.home_path == expected_path


@pytest.mark.parametrize("maxsize, is_32bit", [(2**32, True), (2**64, False)])
def test_is_32bit_python(maxsize, is_32bit, monkeypatch, tmp_path):
    """Whether Python is 32bits is sensitive to `sys.maxsize`."""
    monkeypatch.setattr(sys, "maxsize", maxsize)

    tools = ToolCache(
        console=Console(),
        base_path=tmp_path,
    )

    assert tools.is_32bit_python is is_32bit


@pytest.mark.parametrize(
    "mock_encoding, expected_encoding",
    [
        ("iso-123", "ISO-123"),
        ("", "ISO-4242"),
        (None, "ISO-4242"),
    ],
)
def test_system_encoding(simple_tools, mock_encoding, expected_encoding, monkeypatch):
    """The expected system encoding is returned."""
    if sys.version_info < (3, 11):
        monkeypatch.setattr(
            locale, "getdefaultlocale", MagicMock(return_value=("aa_BB", mock_encoding))
        )
    else:
        monkeypatch.setattr(
            locale, "getencoding", MagicMock(return_value=mock_encoding)
        )
    monkeypatch.setattr(
        briefcase.integrations.base, "DEFAULT_SYSTEM_ENCODING", "ISO-4242"
    )
    assert simple_tools.system_encoding == expected_encoding
