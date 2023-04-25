import pytest

from briefcase.exceptions import MissingToolError, NonManagedToolError
from briefcase.integrations.base import Tool


@pytest.fixture
def unmanaged_tool(mock_tools) -> Tool:
    class DummyTool(Tool):
        """Unmanaged Tool testing class."""

        name = "UnmanagedDummyTool"
        full_name = "Unmanaged Dummy Tool"

        def verify(self, tools):
            pass

    return DummyTool(tools=mock_tools)


@pytest.fixture
def managed_tool(mock_tools) -> Tool:
    class DummyTool(Tool):
        """Managed Tool testing class."""

        name = "ManagedDummyTool"
        full_name = "Managed Dummy Tool"
        managed_install = True

        def verify(self, tools):
            pass

    return DummyTool(tools=mock_tools)


def test_exists_raises(unmanaged_tool):
    """Tool.exists() raises NotImplementedError when not defined in subclass."""
    with pytest.raises(
        NotImplementedError,
        match="Missing implementation for Tool 'DummyTool'",
    ):
        unmanaged_tool.exists()


def test_managed_install_defaults_false(unmanaged_tool):
    """Tool.managed_install defaults False."""
    assert unmanaged_tool.managed_install is False


def test_install_raises_for_managed_tool(managed_tool):
    """Tool.install() raises NotImplementedError for managed tool."""
    with pytest.raises(
        NotImplementedError, match="Missing implementation for Tool 'DummyTool'"
    ):
        managed_tool.install()


def test_install_raises_for_unmanaged_tool(unmanaged_tool):
    """Tool.install() raises NonManagedToolError for unmanaged tool."""
    with pytest.raises(
        NonManagedToolError,
        match="'Unmanaged Dummy Tool' is using an install that is user managed.",
    ):
        unmanaged_tool.install()


def test_uninstall_raises_for_managed_tool(managed_tool):
    """Tool.uninstall() raises NotImplementedError for managed tool."""
    with pytest.raises(
        NotImplementedError,
        match="Missing implementation for Tool 'DummyTool'",
    ):
        managed_tool.uninstall()


def test_uninstall_raises_for_unmanaged_tool(unmanaged_tool):
    """Tool.uninstall() raises NonManagedToolError for unmanaged tool."""
    with pytest.raises(
        NonManagedToolError,
        match="'Unmanaged Dummy Tool' is using an install that is user managed.",
    ):
        unmanaged_tool.uninstall()


def test_upgrade_raises_for_managed_tool_when_exists(managed_tool):
    """Tool.upgrade() raises NotImplementedError for managed tool when it exists."""
    managed_tool.exists = lambda: True
    with pytest.raises(
        NotImplementedError,
        match="Missing implementation for Tool 'DummyTool'",
    ):
        managed_tool.upgrade()


def test_upgrade_raises_for_managed_tool_when_not_exists(managed_tool):
    """Tool.upgrade() raises MissingToolError for managed tool when it does not
    exist."""
    managed_tool.exists = lambda: False
    with pytest.raises(
        MissingToolError,
        match="Unable to locate 'Managed Dummy Tool'. Has it been installed?",
    ):
        managed_tool.upgrade()


def test_upgrade_raises_for_unmanaged_tool(unmanaged_tool):
    """Tool.upgrade() raises NonManagedToolError for unmanaged tool."""
    with pytest.raises(
        NonManagedToolError,
        match="'Unmanaged Dummy Tool' is using an install that is user managed.",
    ):
        unmanaged_tool.upgrade()
