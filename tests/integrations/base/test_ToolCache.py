import importlib
import inspect
import os
import pkgutil
import platform
import shutil
import sys
from pathlib import Path

import pytest
import requests
from cookiecutter.main import cookiecutter

import briefcase.integrations
from briefcase.console import Console, Log
from briefcase.integrations.base import Tool, ToolCache


@pytest.fixture
def simple_tools(tmp_path):
    return ToolCache(
        logger=Log(),
        console=Console(),
        base_path=tmp_path,
    )


def tools_for_module(tool_module_name: str) -> set:
    """Return names of classes that subclass Tool in a module in
    ``briefcase.integrations``, e.g. "android_sdk"."""
    return {
        klass_name
        for klass_name, _ in inspect.getmembers(
            sys.modules[f"briefcase.integrations.{tool_module_name}"],
            lambda klass: (
                inspect.isclass(klass) and issubclass(klass, Tool) and klass is not Tool
            ),
        )
    }


def test_toolcache_typing():
    """Tool typing for ToolCache is correct."""
    # Modules in ``briefcase.integrations`` that do not contain tools.
    nontool_modules = {"base"}
    # Tools that are intentionally not annotated in ToolCache.
    tools_unannotated = {"cookiecutter"}
    # Tool names to exclude from the dynamic annotation checks; they are manually checked.
    tool_names_skip_dynamic_check = {"app_context", "git", "xcode", "xcode_cli"}
    # Tool classes to exclude from dynamic annotation checks.
    tool_klasses_skip_dynamic_checks = {"DockerAppContext", "NativeAppContext"}

    # Ensure all modules containing Tools are exported in ``briefcase.integrations``.
    tool_modules = {
        module.name
        for module in pkgutil.iter_modules(briefcase.integrations.__path__)
        if module.name not in nontool_modules
    }
    assert sorted(tool_modules) == sorted(briefcase.integrations.__all__)

    # Ensure defined Tool modules/classes are annotated in ToolCache.
    for tool_module_name in briefcase.integrations.__all__:
        if tool_module_name not in tools_unannotated:
            assert tool_module_name in ToolCache.__annotations__.keys()
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

    assert ToolCache.__annotations__["xcode"] == "bool"
    assert ToolCache.__annotations__["xcode_cli"] == "bool"

    assert ToolCache.__annotations__["git"] == "git_"


def test_third_party_tools_available():
    """Third party tools are available."""
    assert ToolCache.os is os
    assert ToolCache.platform is platform
    assert ToolCache.shutil is shutil
    assert ToolCache.sys is sys

    assert ToolCache.cookiecutter is cookiecutter
    assert ToolCache.requests is requests


def test_always_true(simple_tools, tmp_path):
    """Implicit boolean casts are always True."""
    assert simple_tools or False
    simple_tools["app-1"].app_context = "tool"
    assert simple_tools["app-1"] or False


def test_mapping_protocol(simple_tools):
    """ToolCache is a mapping."""
    simple_tools["app-1"].tool = "tool 1"
    simple_tools["app-2"].tool = "tool 2"

    assert [app for app in simple_tools] == ["app-1", "app-2"]
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
        logger=Log(),
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
        logger=Log(),
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
        logger=Log(),
        console=Console(),
        base_path=tmp_path,
        home_path=home_path,
    )
    assert tools.home_path == expected_path
