import os
from pathlib import Path

import pytest

from briefcase.config import LinuxDeployPlugin, LinuxDeployPluginType
from briefcase.exceptions import BriefcaseCommandError


def test_list_tools(
    upgrade_command, ManagedSDK1, ManagedSDK2, NonManagedSDK, NonInstalledSDK, capsys
):
    """The tools for upgrade can be listed."""

    upgrade_command(tool_list=[], list_tools=True)

    # The tools are all verified
    ManagedSDK1.verify.assert_called_with(upgrade_command, install=False)
    ManagedSDK2.verify.assert_called_with(upgrade_command, install=False)
    NonManagedSDK.verify.assert_called_with(upgrade_command, install=False)
    NonInstalledSDK.verify.assert_called_with(upgrade_command, install=False)

    # The console contains the lines we expect, but not the non-managed and
    # non-installed tools.
    out = capsys.readouterr().out
    assert " - managed-1" in out
    assert " - managed-2" in out
    assert " - non-managed" not in out
    assert " - non-installed" not in out


def test_list_specific_tools(
    upgrade_command, ManagedSDK1, ManagedSDK2, NonManagedSDK, NonInstalledSDK, capsys
):
    """If a list of tools is provided, only those are listed."""

    upgrade_command(
        tool_list=["managed-1", "non-managed", "non-installed"], list_tools=True
    )

    # All tools are verified
    ManagedSDK1.verify.assert_called_with(upgrade_command, install=False)
    ManagedSDK2.verify.assert_called_with(upgrade_command, install=False)
    NonManagedSDK.verify.assert_called_with(upgrade_command, install=False)
    NonInstalledSDK.verify.assert_called_with(upgrade_command, install=False)

    # The console contains the lines we expect, but not the non-requested,
    # non-managed, and non-installed tools.
    out = capsys.readouterr().out
    assert " - managed-1" in out
    assert " - managed-2" not in out
    assert " - non-managed" not in out
    assert " - non-installed" not in out


def test_upgrade_tools(
    upgrade_command, ManagedSDK1, ManagedSDK2, NonManagedSDK, NonInstalledSDK, capsys
):
    """All managed tools can be upgraded."""
    upgrade_command(tool_list=[])

    # All tools are verified
    ManagedSDK1.verify.assert_called_with(upgrade_command, install=False)
    ManagedSDK2.verify.assert_called_with(upgrade_command, install=False)
    NonManagedSDK.verify.assert_called_with(upgrade_command, install=False)
    NonInstalledSDK.verify.assert_called_with(upgrade_command, install=False)

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
    upgrade_command, ManagedSDK1, ManagedSDK2, NonManagedSDK, NonInstalledSDK, capsys
):
    """If a list of tools is provided, only those are listed."""

    upgrade_command(
        tool_list=["managed-1", "non-managed", "non-installed"],
    )

    # All tools are verified
    ManagedSDK1.verify.assert_called_with(upgrade_command, install=False)
    ManagedSDK2.verify.assert_called_with(upgrade_command, install=False)
    NonManagedSDK.verify.assert_called_with(upgrade_command, install=False)
    NonInstalledSDK.verify.assert_called_with(upgrade_command, install=False)

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
    upgrade_command, ManagedSDK1, ManagedSDK2, NonManagedSDK, NonInstalledSDK, capsys
):
    """If there is nothing up upgrade, a message is returned."""

    upgrade_command(
        tool_list=["non-managed", "non-installed"],
    )

    # All tools are verified
    ManagedSDK1.verify.assert_called_with(upgrade_command, install=False)
    ManagedSDK2.verify.assert_called_with(upgrade_command, install=False)
    NonManagedSDK.verify.assert_called_with(upgrade_command, install=False)
    NonInstalledSDK.verify.assert_called_with(upgrade_command, install=False)

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
    upgrade_command, ManagedSDK1, ManagedSDK2, NonManagedSDK, NonInstalledSDK, capsys
):
    """If a list of tools is provided, only those are listed."""

    # Requesting an unknown tool raises an error
    with pytest.raises(BriefcaseCommandError):
        upgrade_command(tool_list=["managed-1", "unknown-tool"])

    # All tools are still verified
    ManagedSDK1.verify.assert_called_with(upgrade_command, install=False)
    ManagedSDK2.verify.assert_called_with(upgrade_command, install=False)
    NonManagedSDK.verify.assert_called_with(upgrade_command, install=False)
    NonInstalledSDK.verify.assert_called_with(upgrade_command, install=False)


@pytest.mark.parametrize(
    "linuxdeploy_plugin,type,path,env_var,",
    [
        (["gtk"], LinuxDeployPluginType.GTK, "gtk", None),
        (
            ["https://briefcase.org/linuxdeploy-gtk-plugin.sh"],
            LinuxDeployPluginType.URL,
            "https://briefcase.org/linuxdeploy-gtk-plugin.sh",
            None,
        ),
        (
            ["DEPLOY_GTK_VERSION=3 https://briefcase.org/linuxdeploy-gtk-plugin.sh"],
            LinuxDeployPluginType.URL,
            "https://briefcase.org/linuxdeploy-gtk-plugin.sh",
            "DEPLOY_GTK_VERSION=3",
        ),
    ],
)
def test_upgrade_linuxdeploy_plugin_gtk(
    linuxdeploy_plugin,
    type,
    path,
    env_var,
    upgrade_command,
    ManagedSDK1,
    first_app_config,
    tmpdir,
):
    """Test upgrade of gtk plugin."""
    file_plugin = Path(tmpdir) / "linuxdeploy-gtk-plugin.sh"
    file_plugin.touch()

    first_app_config.linuxdeploy_plugins = linuxdeploy_plugin
    first_app_config.linuxdeploy_plugins_info = [
        LinuxDeployPlugin(type=type, path=path, env_var=env_var)
    ]
    upgrade_command.apps = {
        "first": first_app_config,
    }

    # Run the upgrade command
    upgrade_command(tool_list=["managed-1"])

    # Verify tool
    ManagedSDK1.verify.assert_called_with(upgrade_command, install=False)


def test_upgrade_linuxdeploy_plugin_gtk_file(
    upgrade_command, ManagedSDK1, first_app_config, tmpdir, monkeypatch
):
    """Test upgrade of local file-based gtk plugin."""
    file_plugin = Path(tmpdir) / "linuxdeploy-gtk-plugin.sh"
    file_plugin.touch()

    first_app_config.linuxdeploy_plugins = str(file_plugin)
    first_app_config.linuxdeploy_plugins_info = [
        LinuxDeployPlugin(
            type=LinuxDeployPluginType.FILE, path=str(file_plugin), env_var=None
        )
    ]
    upgrade_command.apps = {
        "first": first_app_config,
    }

    # Do not create hard link during tests
    monkeypatch.setattr(os, "link", lambda src, dst: None)
    monkeypatch.setattr(os, "chmod", lambda path, mode: None)

    # Run the upgrade command
    upgrade_command(tool_list=["managed-1"])

    # Verify tool
    ManagedSDK1.verify.assert_called_with(upgrade_command, install=False)
