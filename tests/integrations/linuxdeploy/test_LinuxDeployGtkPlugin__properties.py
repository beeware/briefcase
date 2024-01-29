import pytest

from briefcase.integrations.linuxdeploy import LinuxDeployGtkPlugin

from ...utils import assert_url_resolvable


@pytest.fixture
def linuxdeploy_gtk_plugin(mock_tools):
    return LinuxDeployGtkPlugin(mock_tools)


def test_file_path(linuxdeploy_gtk_plugin, mock_tools):
    """Default Linuxdeploy plugins reside in the linuxdeploy plugins path."""
    assert (
        linuxdeploy_gtk_plugin.file_path
        == mock_tools.base_path / "linuxdeploy_plugins/gtk"
    )


def test_file_name(linuxdeploy_gtk_plugin):
    """GTK plugin has a known name."""
    assert linuxdeploy_gtk_plugin.file_name == "linuxdeploy-plugin-gtk.sh"


def test_plugin_id(linuxdeploy_gtk_plugin):
    """GTK plugin ID is fixed."""
    assert linuxdeploy_gtk_plugin.plugin_id == "gtk"


def test_download_url(linuxdeploy_gtk_plugin):
    """GTK plugin download URL is architecture dependent."""
    assert linuxdeploy_gtk_plugin.download_url == (
        "https://raw.githubusercontent.com/linuxdeploy/linuxdeploy-plugin-gtk/"
        "master/linuxdeploy-plugin-gtk.sh"
    )
    assert_url_resolvable(linuxdeploy_gtk_plugin.download_url)
