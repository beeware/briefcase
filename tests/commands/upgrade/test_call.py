import pytest

from briefcase.exceptions import BriefcaseCommandError


def test_list_tools(
    upgrade_command,
    ManagedSDK1,
    ManagedSDK2,
    ManagedSDK2Plugin1,
    ManagedSDK2Plugin2,
    ManagedSDK2Plugin3,
    NonManagedSDK,
    NonInstalledSDK,
    capsys,
):
    """The tools for upgrade can be listed."""

    upgrade_command(tool_list=[], list_tools=True)

    # The tools are all verified
    ManagedSDK1.verify.assert_called_with(upgrade_command.tools, install=False)
    ManagedSDK2.verify.assert_called_with(upgrade_command.tools, install=False)
    ManagedSDK2Plugin1.verify.assert_called_with(upgrade_command.tools, install=False)
    ManagedSDK2Plugin2.verify.assert_called_with(upgrade_command.tools, install=False)
    ManagedSDK2Plugin3.verify.assert_called_with(upgrade_command.tools, install=False)
    NonManagedSDK.verify.assert_called_with(upgrade_command.tools, install=False)
    NonInstalledSDK.verify.assert_called_with(upgrade_command.tools, install=False)

    # The console contains the lines we expect, but not the non-managed and
    # non-installed tools.
    out = capsys.readouterr().out
    assert " - managed-1" in out
    assert " - managed-2" in out
    assert " - managed-2-plugin-1" in out
    assert " - managed-2-plugin-2" in out
    assert " - managed-2-plugin-3" not in out
    assert " - non-managed" not in out
    assert " - non-installed" not in out


def test_list_specific_tools(
    upgrade_command,
    ManagedSDK1,
    ManagedSDK2,
    NonManagedSDK,
    NonInstalledSDK,
    capsys,
):
    """If a list of tools is provided, only those are listed."""

    upgrade_command(
        tool_list=["managed-1", "non-managed", "non-installed"], list_tools=True
    )

    # All tools are verified
    ManagedSDK1.verify.assert_called_with(upgrade_command.tools, install=False)
    ManagedSDK2.verify.assert_called_with(upgrade_command.tools, install=False)
    NonManagedSDK.verify.assert_called_with(upgrade_command.tools, install=False)
    NonInstalledSDK.verify.assert_called_with(upgrade_command.tools, install=False)

    # The console contains the lines we expect, but not the non-requested,
    # non-managed, and non-installed tools.
    out = capsys.readouterr().out
    assert " - managed-1" in out
    assert " - managed-2" not in out
    assert " - non-managed" not in out
    assert " - non-installed" not in out


def test_upgrade_tools(
    upgrade_command,
    ManagedSDK1,
    ManagedSDK2,
    NonManagedSDK,
    NonInstalledSDK,
    capsys,
):
    """All managed tools can be upgraded."""
    upgrade_command(tool_list=[])

    # All tools are verified
    ManagedSDK1.verify.assert_called_with(upgrade_command.tools, install=False)
    ManagedSDK2.verify.assert_called_with(upgrade_command.tools, install=False)
    NonManagedSDK.verify.assert_called_with(upgrade_command.tools, install=False)
    NonInstalledSDK.verify.assert_called_with(upgrade_command.tools, install=False)

    # The console contains the lines we expect, but not the non-managed and
    # non-installed tools.
    out = capsys.readouterr().out
    assert " - managed-1" in out
    assert " - managed-2" in out
    assert " - non-managed" not in out
    assert " - non-installed" not in out

    # There is also an upgrade message for each tool
    assert "[managed-1] Upgrading Managed 1..." in out
    assert "[managed-2] Upgrading Managed 2..." in out

    # The managed tools are upgraded
    ManagedSDK1.upgrade.assert_called_with()
    ManagedSDK2.upgrade.assert_called_with()
    assert NonManagedSDK.upgrade.call_count == 0
    assert NonInstalledSDK.upgrade.call_count == 0


def test_upgrade_specific_tools(
    upgrade_command,
    ManagedSDK1,
    ManagedSDK2,
    NonManagedSDK,
    NonInstalledSDK,
    capsys,
):
    """If a list of tools is provided, only those are listed."""

    upgrade_command(
        tool_list=["managed-1", "non-managed", "non-installed"],
    )

    # All tools are verified
    ManagedSDK1.verify.assert_called_with(upgrade_command.tools, install=False)
    ManagedSDK2.verify.assert_called_with(upgrade_command.tools, install=False)
    NonManagedSDK.verify.assert_called_with(upgrade_command.tools, install=False)
    NonInstalledSDK.verify.assert_called_with(upgrade_command.tools, install=False)

    # The console contains the lines we expect, but not the non-requested,
    # non-managed, and non-installed tools.
    out = capsys.readouterr().out
    assert " - managed-1" in out
    assert " - managed-2" not in out
    assert " - non-managed" not in out
    assert " - non-installed" not in out

    # There is also an upgrade message for each tool
    assert "[managed-1] Upgrading Managed 1..." in out

    # The requested managed tools are upgraded
    ManagedSDK1.upgrade.assert_called_with()
    assert ManagedSDK2.upgrade.call_count == 0
    assert NonManagedSDK.upgrade.call_count == 0
    assert NonInstalledSDK.upgrade.call_count == 0


def test_upgrade_no__tools(
    upgrade_command,
    ManagedSDK1,
    ManagedSDK2,
    NonManagedSDK,
    NonInstalledSDK,
    capsys,
):
    """If there is nothing up upgrade, a message is returned."""

    upgrade_command(
        tool_list=["non-managed", "non-installed"],
    )

    # All tools are verified
    ManagedSDK1.verify.assert_called_with(upgrade_command.tools, install=False)
    ManagedSDK2.verify.assert_called_with(upgrade_command.tools, install=False)
    NonManagedSDK.verify.assert_called_with(upgrade_command.tools, install=False)
    NonInstalledSDK.verify.assert_called_with(upgrade_command.tools, install=False)

    # The console contains no mention of tools...
    out = capsys.readouterr().out
    assert " - managed-1" not in out
    assert " - managed-2" not in out
    assert " - non-managed" not in out
    assert " - non-installed" not in out

    # ...but it *does* say there's nothing being managed.
    assert "Briefcase is not managing any tools." in out

    # Nothing is upgraded
    assert ManagedSDK1.upgrade.call_count == 0
    assert ManagedSDK2.upgrade.call_count == 0
    assert NonManagedSDK.upgrade.call_count == 0
    assert NonInstalledSDK.upgrade.call_count == 0


def test_unknown_tool(
    upgrade_command,
    ManagedSDK1,
    ManagedSDK2,
    NonManagedSDK,
    NonInstalledSDK,
    capsys,
):
    """If a list of tools is provided, only those are listed."""

    # Requesting an unknown tool raises an error
    with pytest.raises(BriefcaseCommandError):
        upgrade_command(tool_list=["managed-1", "unknown-tool"])

    # All tools are still verified
    ManagedSDK1.verify.assert_called_with(upgrade_command.tools, install=False)
    ManagedSDK2.verify.assert_called_with(upgrade_command.tools, install=False)
    NonManagedSDK.verify.assert_called_with(upgrade_command.tools, install=False)
    NonInstalledSDK.verify.assert_called_with(upgrade_command.tools, install=False)
