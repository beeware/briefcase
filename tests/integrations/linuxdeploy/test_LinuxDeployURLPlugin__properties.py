import pytest

from briefcase.integrations.linuxdeploy import LinuxDeployURLPlugin


@pytest.fixture
def linuxdeploy_plugin(mock_command):
    return LinuxDeployURLPlugin(
        mock_command,
        url="https://example.com/path/to/linuxdeploy-plugin-foobar.sh",
    )


def test_file_path(mock_command, linuxdeploy_plugin):
    """Custom URL plugins are in the linuxdeploy plugins folder, behind a
    hash."""
    assert (
        linuxdeploy_plugin.file_path
        == mock_command.tools_path
        / "linuxdeploy_plugins"
        / "foobar"
        / "5a8b5d4227212665a4e6bfc04cf3ebb588e491a42e8a2daaceab49191b0f93ea"
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
