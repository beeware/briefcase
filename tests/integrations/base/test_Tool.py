from unittest.mock import MagicMock

import pytest

from briefcase.exceptions import (
    MissingToolError,
    NonManagedToolError,
    UnsupportedHostError,
)
from briefcase.integrations.base import ManagedTool, Tool


class DummyTool(Tool):
    """Unmanaged Tool testing class."""

    name = "UnmanagedDummyTool"
    full_name = "Unmanaged Dummy Tool"
    supported_host_os = {"wonky"}

    @classmethod
    def verify_install(cls, tools, **kwargs):
        return f"i'm a {cls.name}"


class DummyManagedTool(ManagedTool):
    """Managed Tool testing class."""

    name = "ManagedDummyTool"
    full_name = "Managed Dummy Tool"
    supported_host_os = {"wonky"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.actions = []

    @classmethod
    def verify_install(cls, tools, **kwargs):
        return f"i'm a {cls.name}"

    def exists(self) -> bool:
        self.actions.append("exists")
        return True

    def install(self, *args, **kwargs):
        self.actions.append("install")

    def uninstall(self, *args, **kwargs):
        self.actions.append("uninstall")


@pytest.fixture
def unmanaged_tool(mock_tools) -> DummyTool:
    return DummyTool(tools=mock_tools)


@pytest.fixture
def managed_tool(mock_tools) -> DummyManagedTool:
    return DummyManagedTool(tools=mock_tools)


@pytest.mark.parametrize(
    "klass, kwargs",
    [
        (DummyTool, {}),
        (DummyManagedTool, {}),
        (DummyTool, {"one": "two", "three": "four"}),
        (DummyManagedTool, {"one": "two", "three": "four"}),
    ],
)
def test_tool_verify(mock_tools, klass, kwargs, monkeypatch):
    """Tool verification checks host OS and tool install."""
    mock_verify_host = MagicMock(wraps=klass.verify_host)
    mock_verify_install = MagicMock(wraps=klass.verify_install)
    monkeypatch.setattr(klass, "verify_host", mock_verify_host)
    monkeypatch.setattr(klass, "verify_install", mock_verify_install)

    mock_tools.host_os = "wonky"

    tool = klass.verify(tools=mock_tools, **kwargs)

    mock_verify_host.assert_called_once_with(tools=mock_tools)
    mock_verify_install.assert_called_once_with(tools=mock_tools, app=None, **kwargs)
    assert tool == f"i'm a {klass.name}"


@pytest.mark.parametrize(
    "klass, kwargs",
    [
        (DummyTool, {}),
        (DummyManagedTool, {}),
        (DummyTool, {"one": "two", "three": "four"}),
        (DummyManagedTool, {"one": "two", "three": "four"}),
    ],
)
def test_tool_verify_with_app(mock_tools, first_app_config, klass, kwargs, monkeypatch):
    """App-bound Tool verification checks host OS and tool install."""
    mock_verify_host = MagicMock(wraps=klass.verify_host)
    mock_verify_install = MagicMock(wraps=klass.verify_install)
    monkeypatch.setattr(klass, "verify_host", mock_verify_host)
    monkeypatch.setattr(klass, "verify_install", mock_verify_install)

    mock_tools.host_os = "wonky"

    tool = klass.verify(tools=mock_tools, app=first_app_config, **kwargs)

    mock_verify_host.assert_called_once_with(tools=mock_tools)
    mock_verify_install.assert_called_once_with(
        tools=mock_tools,
        app=first_app_config,
        **kwargs,
    )
    assert tool == f"i'm a {klass.name}"


@pytest.mark.parametrize("klass", [DummyTool, DummyManagedTool])
def test_tool_unsupported_host_os(mock_tools, klass):
    """Tool verification fails for unsupported Host OS."""
    mock_tools.host_os = "not wonky"

    with pytest.raises(
        UnsupportedHostError,
        match=f"{klass.name} is not supported on not wonky",
    ):
        klass.verify(tools=mock_tools)


def test_unmanaged_install_is_false(unmanaged_tool):
    """Tool.managed_install defaults False."""
    assert unmanaged_tool.managed_install is False


def test_managed_install_is_true(managed_tool):
    """Tool.managed_install defaults False."""
    assert managed_tool.managed_install is True


def test_managed_upgrade(managed_tool):
    """Order of operations is correct for upgrade."""
    managed_tool.upgrade()

    assert managed_tool.actions == ["exists", "uninstall", "install"]


def test_managed_raises_if_unmanaged(mock_tools):
    """If a ManagedTool is unmanaged, upgrade raises."""

    class NonManagedManagedTool(DummyManagedTool):
        @property
        def managed_install(self) -> bool:
            return False

    with pytest.raises(NonManagedToolError):
        NonManagedManagedTool(tools=mock_tools).upgrade()


def test_managed_raises_if_not_exists(mock_tools):
    """If a ManagedTool doesn't exist, upgrade raises."""

    class NonExistsManagedTool(DummyManagedTool):
        def exists(self) -> bool:
            return False

    with pytest.raises(MissingToolError):
        NonExistsManagedTool(tools=mock_tools).upgrade()
