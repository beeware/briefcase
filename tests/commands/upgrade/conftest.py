from unittest.mock import MagicMock

import pytest

import briefcase.commands.upgrade
from briefcase.commands import UpgradeCommand
from briefcase.console import Console, Log
from briefcase.exceptions import MissingToolError
from briefcase.integrations.base import ManagedTool, Tool


@pytest.fixture
def upgrade_command(tmp_path):
    command = DummyUpgradeCommand(base_path=tmp_path)
    command.tools.host_os = "wonky"
    return command


class DummyUpgradeCommand(UpgradeCommand):
    """A dummy upgrade command that doesn't actually do anything.

    It only serves to track which actions would be performed.
    """

    # Platform and format contain upper case to test case normalization
    platform = "Tester"
    output_format = "Dummy"
    description = "Dummy update command"

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("logger", Log())
        kwargs.setdefault("console", Console())
        super().__init__(*args, **kwargs)

    def bundle_path(self, app):
        return self.platform_path / f"{app.app_name}.dummy"

    def binary_path(self, app):
        return self.bundle_path(app) / f"{app.app_name}.bin"


@pytest.fixture
def mock_tool_registry(monkeypatch):
    """Tool registry with all dummy tools."""
    tool_list = [
        DummyTool,
        DummyManagedTool1,
        DummyManagedTool2,
        DummyManagedTool3,
        DummyUnManagedManagedTool,
        DummyNotInstalledManagedTool,
    ]

    tool_registry = dict()
    for tool in tool_list:
        monkeypatch.setattr(tool, "verify", MagicMock(wraps=tool.verify))
        tool_registry[tool.name] = tool

    monkeypatch.setattr(briefcase.commands.upgrade, "tool_registry", tool_registry)


@pytest.fixture
def mock_no_managed_tool_registry(monkeypatch):
    """Tool registry without any installed managed tools."""
    tool_list = [
        DummyTool,
        DummyUnManagedManagedTool,
        DummyNotInstalledManagedTool,
    ]

    tool_registry = dict()
    for tool in tool_list:
        monkeypatch.setattr(tool, "verify", MagicMock(wraps=tool.verify))
        tool_registry[tool.name] = tool

    monkeypatch.setattr(briefcase.commands.upgrade, "tool_registry", tool_registry)


class DummyToolBase(Tool):
    name = "dummy_tool_base"
    supported_host_os = {"wonky"}

    @classmethod
    def verify_install(cls, tools, **kwargs):
        return cls(tools=tools)


class DummyManagedToolBase(ManagedTool):
    name = "dummy_managed_tool_base"
    supported_host_os = {"wonky"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.actions = []

    @classmethod
    def verify_install(cls, tools, **kwargs):
        # add to ToolCache so accessible after upgrade
        setattr(tools, cls.name, cls(tools=tools))
        return getattr(tools, cls.name)

    def exists(self) -> bool:
        self.actions.append("exists")
        return True

    def install(self):
        self.actions.append("install")

    def uninstall(self):
        self.actions.append("uninstall")


class DummyTool(DummyToolBase):
    """Unmanaged Tool testing class."""

    name = "unmanaged"
    full_name = "Unmanaged Dummy Tool"


class DummyUnManagedManagedTool(DummyManagedToolBase):
    """Managed Tool without a managed install testing class."""

    name = "unmanaged_managed"
    full_name = "Unmanaged Managed Dummy Tool"

    @property
    def managed_install(self) -> bool:
        return False


class DummyNotInstalledManagedTool(DummyManagedToolBase):
    """Managed Tool without a managed install testing class."""

    name = "not_installed"
    full_name = "Not Installed Managed Dummy Tool"

    @classmethod
    def verify_install(cls, tools, **kwargs):
        raise MissingToolError(cls.full_name)


class DummyManagedTool1(DummyManagedToolBase):
    """Managed Tool testing class."""

    name = "managed_1"
    full_name = "Managed Dummy Tool 1"


class DummyManagedTool2(DummyManagedToolBase):
    """Managed Tool testing class."""

    name = "managed_2"
    full_name = "Managed Dummy Tool 2"


class DummyManagedTool3(DummyManagedToolBase):
    """Managed Tool testing class."""

    name = "managed_3"
    full_name = "Managed Dummy Tool 3"
