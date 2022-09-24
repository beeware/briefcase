import pytest

from briefcase.integrations.linuxdeploy import LinuxDeployURLPlugin


@pytest.fixture
def linuxdeploy_plugin(mock_tools):
    return LinuxDeployURLPlugin(
        mock_tools,
        url="https://example.com/path/to/linuxdeploy-plugin-foobar.sh",
    )


def test_file_path(mock_tools, linuxdeploy_plugin):
    """Custom URL plugins are in the linuxdeploy plugins folder, behind a
    hash."""
    assert (
        linuxdeploy_plugin.file_path
        == mock_tools.base_path
        / "linuxdeploy_plugins"
        / "foobar"
        / "dc66c26aaeb8083777d1975e55dfb5c197b5b54e7b46481793eab4b3f2ace1b3"
    )


def test_file_name(linuxdeploy_plugin):
    """Custom URL plugin filenames come from the URL."""
    assert linuxdeploy_plugin.file_name == "linuxdeploy-plugin-foobar.sh"


def test_plugin_id(linuxdeploy_plugin):
    """The Custom URL plugin ID can be determined from the filename."""
    assert linuxdeploy_plugin.plugin_id == "foobar"


def test_download_url(linuxdeploy_plugin):
    """The download URL for the plugin is as-provided."""
    assert linuxdeploy_plugin.download_url == (
        "https://example.com/path/to/linuxdeploy-plugin-foobar.sh"
    )
