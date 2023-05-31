import pytest

from briefcase.integrations.linuxdeploy import LinuxDeployQtPlugin


@pytest.fixture
def linuxdeploy_qt_plugin(mock_tools):
    return LinuxDeployQtPlugin(mock_tools)


def test_file_path(mock_tools, linuxdeploy_qt_plugin):
    """Default Linuxdeploy plugins reside in the linuxdeploy plugins path."""
    assert (
        linuxdeploy_qt_plugin.file_path
        == mock_tools.base_path / "linuxdeploy_plugins" / "qt"
    )


def test_file_name(linuxdeploy_qt_plugin):
    """Linuxdeploy Qt plugin filename is architecture dependent."""
    assert linuxdeploy_qt_plugin.file_name == "linuxdeploy-plugin-qt-wonky.AppImage"


def test_plugin_id(linuxdeploy_qt_plugin):
    """Linuxdeploy Qt plugin ID is fixed."""
    assert linuxdeploy_qt_plugin.plugin_id == "qt"


def test_download_url(linuxdeploy_qt_plugin):
    """Linuxdeploy Qt plugin download URL is architecture dependent."""
    assert linuxdeploy_qt_plugin.download_url == (
        "https://github.com/linuxdeploy/linuxdeploy-plugin-qt/"
        "releases/download/continuous/linuxdeploy-plugin-qt-wonky.AppImage"
    )
