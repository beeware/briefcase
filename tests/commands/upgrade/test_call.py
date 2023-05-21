import pytest

from briefcase.exceptions import UpgradeToolError

from .conftest import (
    DummyManagedTool1,
    DummyManagedTool2,
    DummyManagedTool3,
    DummyNotInstalledManagedTool,
    DummyTool,
    DummyUnManagedManagedTool,
)


def test_list_tools(upgrade_command, mock_tool_registry, capsys):
    """The tools for upgrade can be listed."""
    upgrade_command(tool_list=[], list_tools=True)

    # Tools that are *not* relevant to this upgrade call are not verified
    DummyTool.verify.assert_not_called()

    # Tools that *are* relevant to this upgrade call are verified
    DummyUnManagedManagedTool.verify.assert_called_once_with(
        tools=upgrade_command.tools, install=False
    )
    DummyNotInstalledManagedTool.verify.assert_called_once_with(
        tools=upgrade_command.tools, install=False
    )
    DummyManagedTool1.verify.assert_called_once_with(
        tools=upgrade_command.tools, install=False
    )
    DummyManagedTool2.verify.assert_called_once_with(
        tools=upgrade_command.tools, install=False
    )
    DummyManagedTool3.verify.assert_called_once_with(
        tools=upgrade_command.tools, install=False
    )

    assert capsys.readouterr().out == (
        "\n"
        "[upgrade] Briefcase is managing the following tools:\n"
        " - Managed Dummy Tool 1 (managed_1)\n"
        " - Managed Dummy Tool 2 (managed_2)\n"
        " - Managed Dummy Tool 3 (managed_3)\n"
    )


def test_list_specific_tools(upgrade_command, mock_tool_registry, capsys):
    """If a list of tools is provided, only those are listed."""
    upgrade_command(tool_list=["managed_1", "managed_2"], list_tools=True)

    # Tools that are *not* relevant to this upgrade call are not verified
    DummyTool.verify.assert_not_called()
    DummyUnManagedManagedTool.verify.assert_not_called()
    DummyNotInstalledManagedTool.verify.assert_not_called()
    DummyManagedTool3.verify.assert_not_called()

    # Tools that *are* relevant to this upgrade call are verified
    DummyManagedTool1.verify.assert_called_once_with(
        tools=upgrade_command.tools, install=False
    )
    DummyManagedTool2.verify.assert_called_once_with(
        tools=upgrade_command.tools, install=False
    )

    assert capsys.readouterr().out == (
        "\n"
        "[upgrade] Briefcase is managing the following tools:\n"
        " - Managed Dummy Tool 1 (managed_1)\n"
        " - Managed Dummy Tool 2 (managed_2)\n"
    )


def test_upgrade_tools(upgrade_command, mock_tool_registry, capsys):
    """All managed tools can be upgraded."""
    upgrade_command(tool_list=[])

    # Tools that are *not* relevant to this upgrade call are not verified
    DummyTool.verify.assert_not_called()

    # Tools that *are* relevant to this upgrade call are verified
    DummyUnManagedManagedTool.verify.assert_called_once_with(
        tools=upgrade_command.tools, install=False
    )
    DummyNotInstalledManagedTool.verify.assert_called_once_with(
        tools=upgrade_command.tools, install=False
    )
    DummyManagedTool1.verify.assert_called_once_with(
        tools=upgrade_command.tools, install=False
    )
    DummyManagedTool2.verify.assert_called_once_with(
        tools=upgrade_command.tools, install=False
    )
    DummyManagedTool3.verify.assert_called_once_with(
        tools=upgrade_command.tools, install=False
    )

    # Tools that are *not* relevant to this upgrade call are not upgraded
    assert upgrade_command.tools.unmanaged_managed.actions == []

    # Tools that *are* relevant to this upgrade call are upgraded
    assert upgrade_command.tools.managed_1.actions == [
        "exists",
        "uninstall",
        "install",
    ]
    assert upgrade_command.tools.managed_2.actions == [
        "exists",
        "uninstall",
        "install",
    ]
    assert upgrade_command.tools.managed_3.actions == [
        "exists",
        "uninstall",
        "install",
    ]

    assert capsys.readouterr().out == (
        "\n"
        "[upgrade] Briefcase will upgrade the following tools:\n"
        " - Managed Dummy Tool 1 (managed_1)\n"
        " - Managed Dummy Tool 2 (managed_2)\n"
        " - Managed Dummy Tool 3 (managed_3)\n"
        "\n"
        "[managed_1] Upgrading Managed Dummy Tool 1...\n"
        "\n"
        "[managed_2] Upgrading Managed Dummy Tool 2...\n"
        "\n"
        "[managed_3] Upgrading Managed Dummy Tool 3...\n"
    )


def test_upgrade_specific_tools(upgrade_command, mock_tool_registry, capsys):
    """If a list of tools is provided, only those are listed."""
    upgrade_command(tool_list=["managed_1", "managed_2"])

    # Tools that are *not* relevant to this upgrade call are not verified
    DummyTool.verify.assert_not_called()
    DummyUnManagedManagedTool.verify.assert_not_called()
    DummyNotInstalledManagedTool.verify.assert_not_called()
    DummyManagedTool3.verify.assert_not_called()

    # Tools that *are* relevant to this upgrade call are verified
    DummyManagedTool1.verify.assert_called_once_with(
        tools=upgrade_command.tools, install=False
    )
    DummyManagedTool2.verify.assert_called_once_with(
        tools=upgrade_command.tools, install=False
    )

    # Tools that *are* relevant to this upgrade call are upgraded
    assert upgrade_command.tools.managed_1.actions == [
        "exists",
        "uninstall",
        "install",
    ]
    assert upgrade_command.tools.managed_2.actions == [
        "exists",
        "uninstall",
        "install",
    ]

    assert capsys.readouterr().out == (
        "\n"
        "[upgrade] Briefcase will upgrade the following tools:\n"
        " - Managed Dummy Tool 1 (managed_1)\n"
        " - Managed Dummy Tool 2 (managed_2)\n"
        "\n"
        "[managed_1] Upgrading Managed Dummy Tool 1...\n"
        "\n"
        "[managed_2] Upgrading Managed Dummy Tool 2...\n"
    )


def test_upgrade_no_tools(upgrade_command, mock_no_managed_tool_registry, capsys):
    """If no tools are being managed, a message is returned."""
    upgrade_command(tool_list=[])

    # Tools that are *not* relevant to this upgrade call are not verified
    DummyTool.verify.assert_not_called()

    # Tools that *are* relevant to this upgrade call are verified
    DummyUnManagedManagedTool.verify.assert_called_once_with(
        tools=upgrade_command.tools, install=False
    )
    DummyNotInstalledManagedTool.verify.assert_called_once_with(
        tools=upgrade_command.tools, install=False
    )

    assert capsys.readouterr().out == "Briefcase is not managing any tools.\n"


def test_upgrade_unmanaged_tools(upgrade_command, mock_tool_registry, capsys):
    """If only unmanaged tools are requested to upgrade, error is raised."""
    with pytest.raises(
        UpgradeToolError,
        match="Briefcase is not managing not_installed, unmanaged, unmanaged_managed.",
    ):
        upgrade_command(tool_list=["unmanaged", "unmanaged_managed", "not_installed"])

    # Tools that are *not* relevant to this upgrade call are not verified
    DummyTool.verify.assert_not_called()
    DummyManagedTool1.verify.assert_not_called()
    DummyManagedTool2.verify.assert_not_called()
    DummyManagedTool3.verify.assert_not_called()

    # Tools that *are* relevant to this upgrade call are verified
    DummyUnManagedManagedTool.verify.assert_called_once_with(
        tools=upgrade_command.tools, install=False
    )
    DummyNotInstalledManagedTool.verify.assert_called_once_with(
        tools=upgrade_command.tools, install=False
    )

    assert capsys.readouterr().out == ""


def test_upgrade_mixed_tools(upgrade_command, mock_tool_registry, capsys):
    """If managed and unmanaged tools are requested to upgrade, a warning is shown and
    the upgrade continues."""
    upgrade_command(
        tool_list=[
            "managed_1",
            "managed_2",
            "unmanaged",
            "unmanaged_managed",
            "not_installed",
        ]
    )

    # Tools that are *not* relevant to this upgrade call are not verified
    DummyTool.verify.assert_not_called()
    DummyManagedTool3.verify.assert_not_called()

    # Tools that *are* relevant to this upgrade call are verified
    DummyUnManagedManagedTool.verify.assert_called_once_with(
        tools=upgrade_command.tools, install=False
    )
    DummyNotInstalledManagedTool.verify.assert_called_once_with(
        tools=upgrade_command.tools, install=False
    )

    # Tools that are *not* relevant to this upgrade call are not upgraded
    assert upgrade_command.tools.unmanaged_managed.actions == []

    # Tools that *are* relevant to this upgrade call are upgraded
    assert upgrade_command.tools.managed_1.actions == [
        "exists",
        "uninstall",
        "install",
    ]
    assert upgrade_command.tools.managed_2.actions == [
        "exists",
        "uninstall",
        "install",
    ]

    assert capsys.readouterr().out == (
        "Briefcase is not managing not_installed, unmanaged, unmanaged_managed.\n"
        "\n"
        "[upgrade] Briefcase will upgrade the following tools:\n"
        " - Managed Dummy Tool 1 (managed_1)\n"
        " - Managed Dummy Tool 2 (managed_2)\n"
        "\n"
        "[managed_1] Upgrading Managed Dummy Tool 1...\n"
        "\n"
        "[managed_2] Upgrading Managed Dummy Tool 2...\n"
    )


def test_unknown_tool(upgrade_command, mock_tool_registry, capsys):
    """An upgrade attempt for an unknown tool raises an error."""

    with pytest.raises(
        UpgradeToolError,
        match="Briefcase does not know how to manage unknown_tool_1, unknown_tool_2.",
    ):
        upgrade_command(tool_list=["managed_1", "unknown_tool_1", "unknown_tool_2"])

    # Tools that are *not* relevant to this upgrade call are not verified
    DummyTool.verify.assert_not_called()
    DummyManagedTool1.verify.assert_not_called()
    DummyManagedTool2.verify.assert_not_called()
    DummyManagedTool3.verify.assert_not_called()
    DummyUnManagedManagedTool.verify.assert_not_called()
    DummyNotInstalledManagedTool.verify.assert_not_called()

    assert capsys.readouterr().out == ""
