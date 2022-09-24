import pytest

from briefcase.integrations.linuxdeploy import LinuxDeployGtkPlugin


@pytest.fixture
def linuxdeploy_plugin(mock_tools):
    return LinuxDeployGtkPlugin(mock_tools)


def test_file_path(linuxdeploy_plugin, mock_tools):
    """Default Linuxdeploy plugins reside in the linuxdeploy plugins path."""
    assert (
        linuxdeploy_plugin.file_path
        == mock_tools.base_path / "linuxdeploy_plugins" / "gtk"
    )


def test_file_name(linuxdeploy_plugin):
    """GTK plugin has a known name."""
    assert linuxdeploy_plugin.file_name == "linuxdeploy-plugin-gtk.sh"


def test_plugin_id(linuxdeploy_plugin):
    """GTK plugin ID is fixed."""
    assert linuxdeploy_plugin.plugin_id == "gtk"


def test_download_url(linuxdeploy_plugin):
    """GTK plugin download URL is architecture dependent."""
    assert linuxdeploy_plugin.download_url == (
        "https://raw.githubusercontent.com/linuxdeploy/linuxdeploy-plugin-gtk/"
        "master/linuxdeploy-plugin-gtk.sh"
    )
