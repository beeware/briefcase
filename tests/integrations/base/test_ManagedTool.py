from unittest.mock import MagicMock

import pytest

from briefcase.exceptions import (
    MissingToolError,
    NonManagedToolError,
    UnsupportedHostError,
)
from briefcase.integrations.base import ManagedTool


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

    def install(self):
        self.actions.append("install")

    def uninstall(self):
        self.actions.append("uninstall")


class NonExistsManagedTool(DummyManagedTool):
    def exists(self) -> bool:
        return False


class NonManagedManagedTool(DummyManagedTool):
    @property
    def managed_install(self) -> bool:
        return False


@pytest.fixture
def managed_tool(mock_tools) -> DummyManagedTool:
    return DummyManagedTool(tools=mock_tools)


@pytest.fixture
def nonexistent_managed_tool(mock_tools) -> NonExistsManagedTool:
    return NonExistsManagedTool(tools=mock_tools)


@pytest.fixture
def nonmanaged_managed_tool(mock_tools) -> NonManagedManagedTool:
    return NonManagedManagedTool(tools=mock_tools)


@pytest.mark.parametrize(
    "klass, kwargs",
    [
        (DummyManagedTool, {}),
        (DummyManagedTool, {"one": "two", "three": "four"}),
    ],
)
def test_tool_verify(mock_tools, klass, kwargs, monkeypatch):
    """Tool verification checks host OS and tool install."""
    # Wrap verify calls to confirm they were called
    mock_verify_host = MagicMock(wraps=klass.verify_host)
    monkeypatch.setattr(klass, "verify_host", mock_verify_host)
    mock_verify_install = MagicMock(wraps=klass.verify_install)
    monkeypatch.setattr(klass, "verify_install", mock_verify_install)

    # Mock the dummy tool's supported OS
    mock_tools.host_os = "wonky"

    tool = klass.verify(tools=mock_tools, **kwargs)

    mock_verify_host.assert_called_once_with(tools=mock_tools)
    mock_verify_install.assert_called_once_with(
        tools=mock_tools, app=None, install=True, **kwargs
    )
    assert tool == f"i'm a {klass.name}"


@pytest.mark.parametrize(
    "klass, kwargs",
    [
        (DummyManagedTool, {}),
        (DummyManagedTool, {"one": "two", "three": "four"}),
    ],
)
def test_tool_verify_with_app(mock_tools, first_app_config, klass, kwargs, monkeypatch):
    """App-bound Tool verification checks host OS and tool install."""
    # Wrap verify calls to confirm they were called
    mock_verify_host = MagicMock(wraps=klass.verify_host)
    monkeypatch.setattr(klass, "verify_host", mock_verify_host)
    mock_verify_install = MagicMock(wraps=klass.verify_install)
    monkeypatch.setattr(klass, "verify_install", mock_verify_install)

    # Mock the dummy tool's supported OS
    mock_tools.host_os = "wonky"

    tool = klass.verify(tools=mock_tools, app=first_app_config, **kwargs)

    mock_verify_host.assert_called_once_with(tools=mock_tools)
    mock_verify_install.assert_called_once_with(
        tools=mock_tools,
        app=first_app_config,
        install=True,
        **kwargs,
    )
    assert tool == "i'm a ManagedDummyTool"


def test_tool_unsupported_host_os(mock_tools):
    """Tool verification fails for unsupported Host OS."""
    mock_tools.host_os = "not wonky"

    with pytest.raises(
        UnsupportedHostError,
        match="ManagedDummyTool is not supported on not wonky",
    ):
        DummyManagedTool.verify(tools=mock_tools)


def test_managed_install_is_true(managed_tool):
    """Tool.managed_install defaults False."""
    assert managed_tool.managed_install is True


def test_managed_upgrade(managed_tool):
    """Order of operations is correct for upgrade."""
    managed_tool.upgrade()

    assert managed_tool.actions == ["exists", "uninstall", "install"]


def test_managed_raises_if_unmanaged(mock_tools, nonmanaged_managed_tool):
    """If a ManagedTool is unmanaged, upgrade raises."""
    with pytest.raises(NonManagedToolError):
        nonmanaged_managed_tool.upgrade()


def test_managed_raises_if_not_exists(mock_tools, nonexistent_managed_tool):
    """If a ManagedTool doesn't exist, upgrade raises."""
    with pytest.raises(MissingToolError):
        nonexistent_managed_tool.upgrade()
