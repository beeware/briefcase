import pytest

from briefcase.integrations.linuxdeploy import LinuxDeployQtPlugin

from ...utils import assert_url_resolvable


@pytest.fixture
def linuxdeploy_qt_plugin(mock_tools):
    return LinuxDeployQtPlugin(mock_tools)


def test_file_path(mock_tools, linuxdeploy_qt_plugin):
    """Default Linuxdeploy plugins reside in the linuxdeploy plugins path."""
    assert (
        linuxdeploy_qt_plugin.file_path
        == mock_tools.base_path / "linuxdeploy_plugins/qt"
    )


@pytest.mark.parametrize(
    "host_os, host_arch, linuxdeploy_arch",
    [
        ("Linux", "x86_64", "x86_64"),
        ("Linux", "i686", "i386"),
        ("Darwin", "x86_64", "x86_64"),
    ],
)
def test_file_name(mock_tools, host_os, host_arch, linuxdeploy_arch):
    """Linuxdeploy Qt plugin filename is architecture dependent."""
    mock_tools.host_os = host_os
    mock_tools.host_arch = host_arch

    linuxdeploy_qt_plugin = LinuxDeployQtPlugin(mock_tools)
    assert (
        linuxdeploy_qt_plugin.file_name
        == f"linuxdeploy-plugin-qt-{linuxdeploy_arch}.AppImage"
    )


def test_plugin_id(linuxdeploy_qt_plugin):
    """Linuxdeploy Qt plugin ID is fixed."""
    assert linuxdeploy_qt_plugin.plugin_id == "qt"


@pytest.mark.parametrize(
    "host_os, host_arch, linuxdeploy_arch",
    [
        ("Linux", "x86_64", "x86_64"),
        ("Linux", "i686", "i386"),
        ("Darwin", "x86_64", "x86_64"),
    ],
)
def test_download_url(mock_tools, host_os, host_arch, linuxdeploy_arch):
    """Linuxdeploy Qt plugin download URL is architecture dependent."""
    mock_tools.host_os = host_os
    mock_tools.host_arch = host_arch

    linuxdeploy_qt_plugin = LinuxDeployQtPlugin(mock_tools)

    assert linuxdeploy_qt_plugin.download_url == (
        "https://github.com/linuxdeploy/linuxdeploy-plugin-qt/"
        f"releases/download/continuous/linuxdeploy-plugin-qt-{linuxdeploy_arch}.AppImage"
    )
    assert_url_resolvable(linuxdeploy_qt_plugin.download_url)
