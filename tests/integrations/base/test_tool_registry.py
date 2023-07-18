import inspect
import pkgutil
import sys
from typing import Dict, Set, Type

import pytest

import briefcase.integrations
from briefcase.integrations.base import ManagedTool, Tool, tool_registry


def integrations_modules() -> Set[str]:
    """All modules in ``briefcase.integrations`` irrespective of whether they are
    defined in ``briefcase.integrations.__all__``"""
    return {
        module.name
        for module in pkgutil.iter_modules(briefcase.integrations.__path__)
        if module.name not in {"base"}
    }


def tools_for_module(tool_module_name: str) -> Dict[str, Type[Tool]]:
    """Return classes that subclass Tool in a module in ``briefcase.integrations``, e.g.
    {"android_sdk": AndroidSDK}."""
    return dict(
        inspect.getmembers(
            sys.modules[f"briefcase.integrations.{tool_module_name}"],
            lambda klass: (
                inspect.isclass(klass)
                and issubclass(klass, (Tool, ManagedTool))
                and klass not in {Tool, ManagedTool}
            ),
        )
    )


@pytest.fixture
def all_defined_tools() -> Set[Type[Tool]]:
    """All classes under ``briefcase.integrations`` that subclass Tool."""
    return {
        tool
        for toolset in map(tools_for_module, integrations_modules())
        for tool in toolset.values()
    }


def test_tool_registry(all_defined_tools, simple_tools):
    """The Tool Registry must contain all defined Tools."""
    # test uses subset since registry will contain dummy testing tools
    assert all_defined_tools.issubset(tool_registry.values())


def test_unique_tool_names(all_defined_tools):
    """All tools must have a unique name."""
    assert len(all_defined_tools) == len({t.name for t in all_defined_tools})


def test_valid_tool_names(all_defined_tools):
    """All tools must have a name without spaces."""
    assert all(" " not in t.name for t in all_defined_tools)
