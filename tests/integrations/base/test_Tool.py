import pytest

from briefcase.integrations.base import ManagedTool, Tool


@pytest.fixture
def unmanaged_tool(mock_tools) -> Tool:
    class DummyTool(Tool):
        """Unmanaged Tool testing class."""

        name = "UnmanagedDummyTool"
        full_name = "Unmanaged Dummy Tool"

        def verify_install(self, tools, **kwargs):
            pass

    return DummyTool(tools=mock_tools)


@pytest.fixture
def managed_tool(mock_tools) -> ManagedTool:
    class DummyTool(ManagedTool):
        """Managed Tool testing class."""

        name = "ManagedDummyTool"
        full_name = "Managed Dummy Tool"
        managed_install = True

        def verify_install(self, tools, **kwargs):
            pass

        def exists(self) -> bool:
            pass

        def install(self, *args, **kwargs):
            pass

        def uninstall(self, *args, **kwargs):
            pass

    return DummyTool(tools=mock_tools)


# def test_managed_install_defaults_false(unmanaged_tool):
#     """Tool.managed_install defaults False."""
#     assert unmanaged_tool.managed_install is False
#
#
# def test_install_raises_for_managed_tool(managed_tool):
#     """Tool.install() raises NotImplementedError for managed tool."""
#     with pytest.raises(
#         NotImplementedError,
#         match="Missing implementation for Tool 'DummyTool'",
#     ):
#         managed_tool.install()
#
#
# def test_uninstall_raises_for_managed_tool(managed_tool):
#     """Tool.uninstall() raises NotImplementedError for managed tool."""
#     with pytest.raises(
#         NotImplementedError,
#         match="Missing implementation for Tool 'DummyTool'",
#     ):
#         managed_tool.uninstall()
#
#
# def test_upgrade_raises_for_managed_tool_when_exists(managed_tool):
#     """Tool.upgrade() raises NotImplementedError for managed tool when it exists."""
#     managed_tool.exists = lambda: True
#     with pytest.raises(
#         NotImplementedError,
#         match="Missing implementation for Tool 'DummyTool'",
#     ):
#         managed_tool.upgrade()
#
#
# def test_upgrade_raises_for_managed_tool_when_not_exists(managed_tool):
#     """Tool.upgrade() raises MissingToolError for managed tool when it does not
#     exist."""
#     managed_tool.exists = lambda: False
#     with pytest.raises(
#         MissingToolError,
#         match="Unable to locate 'Managed Dummy Tool'. Has it been installed?",
#     ):
#         managed_tool.upgrade()
