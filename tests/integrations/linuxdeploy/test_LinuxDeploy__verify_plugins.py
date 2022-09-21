import os
import sys
from unittest.mock import MagicMock

import pytest

from briefcase.integrations.linuxdeploy import (
    LinuxDeploy,
    LinuxDeployGtkPlugin,
    LinuxDeployLocalFilePlugin,
    LinuxDeployQtPlugin,
    LinuxDeployURLPlugin,
)

from .utils import (
    create_mock_appimage,
    side_effect_create_mock_appimage,
    side_effect_create_mock_tool,
)


@pytest.fixture
def linuxdeploy(mock_tools):
    return LinuxDeploy(mock_tools)


def test_no_plugins(linuxdeploy, mock_tools, tmp_path):
    """If there are no plugins, verify is a no-op."""

    plugins = linuxdeploy.verify_plugins([], bundle_path=tmp_path / "bundle")

    mock_tools.download.file.assert_not_called()

    assert plugins == {}


def test_gtk_plugin(linuxdeploy, mock_tools, tmp_path):
    """The GTK plugin can be verified."""

    # Mock a successful download
    mock_tools.download.file.side_effect = side_effect_create_mock_tool(
        tmp_path / "tools" / "linuxdeploy_plugins" / "gtk" / "linuxdeploy-plugin-gtk.sh"
    )

    plugins = linuxdeploy.verify_plugins(["gtk"], bundle_path=tmp_path / "bundle")

    assert plugins.keys() == {"gtk"}
    assert isinstance(plugins["gtk"], LinuxDeployGtkPlugin)

    mock_tools.download.file.assert_called_with(
        url="https://raw.githubusercontent.com/linuxdeploy/linuxdeploy-plugin-gtk/master/linuxdeploy-plugin-gtk.sh",
        download_path=tmp_path / "tools" / "linuxdeploy_plugins" / "gtk",
        role="linuxdeploy GTK plugin",
    )


def test_qt_plugin(linuxdeploy, mock_tools, tmp_path):
    """The Qt plugin can be verified."""

    # Mock a successful download
    mock_tools.download.file.side_effect = side_effect_create_mock_appimage(
        tmp_path
        / "tools"
        / "linuxdeploy_plugins"
        / "qt"
        / "linuxdeploy-plugin-qt-wonky.AppImage"
    )

    plugins = linuxdeploy.verify_plugins(["qt"], bundle_path=tmp_path / "bundle")

    assert plugins.keys() == {"qt"}
    assert isinstance(plugins["qt"], LinuxDeployQtPlugin)

    mock_tools.download.file.assert_called_with(
        url=(
            "https://github.com/linuxdeploy/linuxdeploy-plugin-qt/"
            "releases/download/continuous/linuxdeploy-plugin-qt-wonky.AppImage"
        ),
        download_path=tmp_path / "tools" / "linuxdeploy_plugins" / "qt",
        role="linuxdeploy Qt plugin",
    )


def test_custom_url_plugin(linuxdeploy, mock_tools, tmp_path):
    """A Custom URL plugin can be verified."""

    # Mock a successful download
    mock_tools.download.file.side_effect = side_effect_create_mock_appimage(
        tmp_path
        / "tools"
        / "linuxdeploy_plugins"
        / "sometool"
        / "f3355f8e631ffc1abbb7afd37b36315f7846182ca2276c481fb9a43a7f4d239f"
        / "linuxdeploy-plugin-sometool-wonky.AppImage"
    )

    plugins = linuxdeploy.verify_plugins(
        ["https://example.com/path/to/linuxdeploy-plugin-sometool-wonky.AppImage"],
        bundle_path=tmp_path / "bundle",
    )

    assert plugins.keys() == {"sometool"}
    assert isinstance(plugins["sometool"], LinuxDeployURLPlugin)

    mock_tools.download.file.assert_called_with(
        url="https://example.com/path/to/linuxdeploy-plugin-sometool-wonky.AppImage",
        download_path=tmp_path
        / "tools"
        / "linuxdeploy_plugins"
        / "sometool"
        / "f3355f8e631ffc1abbb7afd37b36315f7846182ca2276c481fb9a43a7f4d239f",
        role="user-provided linuxdeploy plugin from URL",
    )


@pytest.mark.skipif(
    sys.platform == "win32",
    reason="Windows paths can't be passed to linuxdeploy",
)
def test_custom_local_file_plugin(linuxdeploy, mock_tools, tmp_path):
    """A Custom local file plugin can be verified."""

    # Create a local file
    plugin_path = (
        tmp_path / "path" / "to" / "linuxdeploy-plugin-sometool-wonky.AppImage"
    )
    create_mock_appimage(plugin_path)

    plugins = linuxdeploy.verify_plugins(
        [os.fsdecode(plugin_path)],
        bundle_path=tmp_path / "bundle",
    )

    assert plugins.keys() == {"sometool"}
    assert isinstance(plugins["sometool"], LinuxDeployLocalFilePlugin)

    # No download happened
    mock_tools.download.file.assert_not_called()
    # But a copy happened
    assert (tmp_path / "bundle" / "linuxdeploy-plugin-sometool-wonky.AppImage").exists()


@pytest.mark.parametrize(
    "plugin_declaration, expected_env",
    [
        # No environment variables
        (
            "gtk",
            {},
        ),
        # Single environment variable
        (
            "FOO=bar gtk",
            {"FOO": "bar"},
        ),
        # Multiple environment variables
        (
            "FOO=bar PORK=ham gtk",
            {"FOO": "bar", "PORK": "ham"},
        ),
        # Space in var escaped with quotes
        (
            "FOO=bar PORK='serrano ham' gtk",
            {"FOO": "bar", "PORK": "serrano ham"},
        ),
        # Space escaped with baskslash
        (
            "FOO=bar PORK=serrano\\ ham gtk",
            {"FOO": "bar", "PORK": "serrano ham"},
        ),
        # Key-only definition
        (
            "FOO=bar PORK gtk",
            {"FOO": "bar", "PORK": ""},
        ),
    ],
)
def test_plugin_env(
    linuxdeploy,
    tmp_path,
    plugin_declaration,
    expected_env,
):
    """All linuxdeploy installs are managed."""
    linuxdeploy.plugins["gtk"].is_elf_file = MagicMock(return_value=False)

    plugins = linuxdeploy.verify_plugins(
        [plugin_declaration],
        bundle_path=tmp_path / "bundle",
    )

    assert plugins.keys() == {"gtk"}
    assert isinstance(plugins["gtk"], LinuxDeployGtkPlugin)
    assert plugins["gtk"].env == expected_env


@pytest.mark.skipif(
    sys.platform == "win32",
    reason="Windows paths can't be passed to linuxdeploy",
)
def test_complex_plugin_config(linuxdeploy, mock_tools, tmp_path):
    """A complex plugin configuration can be verified."""
    # Define multiple plugins, of different types, each with different environments

    # Three tools are obtained by downloading.
    # We don't want the side effects to occur until the function is invoked;
    # so we need to wrap the side effect callables in another callable.
    def mock_downloads(url, download_path, role):
        if "linuxdeploy_plugins/gtk" in str(download_path):
            return side_effect_create_mock_tool(
                tmp_path
                / "tools"
                / "linuxdeploy_plugins"
                / "gtk"
                / "linuxdeploy-plugin-gtk.sh"
            )(url, download_path, role)
        elif "linuxdeploy_plugins/qt" in str(download_path):
            return side_effect_create_mock_appimage(
                tmp_path
                / "tools"
                / "linuxdeploy_plugins"
                / "qt"
                / "linuxdeploy-plugin-qt-wonky.AppImage"
            )(url, download_path, role)
        elif "linuxdeploy_plugins/network" in str(download_path):
            return side_effect_create_mock_tool(
                tmp_path
                / "tools"
                / "linuxdeploy_plugins"
                / "network"
                / "f93c7e6d04425e4ed7e533655d9898c4984f104711f4ffd3b3966cfc92500b2d"
                / "linuxdeploy-plugin-network.sh"
            )(url, download_path, role)
        else:
            raise Exception("Unexpected download")

    mock_tools.download.file.side_effect = mock_downloads

    # Local file tool is a local file.
    local_plugin_path = (
        tmp_path / "path" / "to" / "linuxdeploy-plugin-sometool-wonky.AppImage"
    )
    create_mock_appimage(local_plugin_path)

    # Verify all the plugins
    plugins = linuxdeploy.verify_plugins(
        [
            "DEPLOY_GTK_VERSION=3 gtk",
            "qt",
            f"QUALITY='really nice' {local_plugin_path}",
            "FOO=bar PORK=ham https://example.com/path/to/linuxdeploy-plugin-network.sh",
        ],
        bundle_path=tmp_path / "bundle",
    )

    assert plugins.keys() == {"gtk", "qt", "sometool", "network"}

    # GTK plugin is as expected
    assert isinstance(plugins["gtk"], LinuxDeployGtkPlugin)
    assert plugins["gtk"].env == {"DEPLOY_GTK_VERSION": "3"}

    # Qt plugin is as expected
    assert isinstance(plugins["qt"], LinuxDeployQtPlugin)
    assert plugins["qt"].env == {}

    # Local file plugin is as expected
    assert isinstance(plugins["sometool"], LinuxDeployLocalFilePlugin)
    assert plugins["sometool"].env == {"QUALITY": "really nice"}
    assert (tmp_path / "bundle" / "linuxdeploy-plugin-sometool-wonky.AppImage").exists()

    # URL plugin is as expected
    assert isinstance(plugins["network"], LinuxDeployURLPlugin)
    assert plugins["network"].env == {"FOO": "bar", "PORK": "ham"}
