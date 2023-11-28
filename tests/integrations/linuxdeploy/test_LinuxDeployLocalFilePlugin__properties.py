import pytest

from briefcase.integrations.linuxdeploy import LinuxDeployLocalFilePlugin


@pytest.fixture
def linuxdeploy_local_file_plugin(mock_tools, tmp_path):
    return LinuxDeployLocalFilePlugin(
        mock_tools,
        plugin_path=tmp_path / "path/to/linuxdeploy-plugin-custom.sh",
        bundle_path=tmp_path / "bundle",
    )


def test_file_path(linuxdeploy_local_file_plugin, tmp_path):
    """Local file plugins are kept in the bundle."""
    assert linuxdeploy_local_file_plugin.file_path == tmp_path / "bundle"


def test_file_name(linuxdeploy_local_file_plugin):
    """Local file plugin filename is as provided."""
    assert linuxdeploy_local_file_plugin.file_name == "linuxdeploy-plugin-custom.sh"


def test_plugin_id(linuxdeploy_local_file_plugin):
    """The custom plugin ID can be determined from the filename."""
    assert linuxdeploy_local_file_plugin.plugin_id == "custom"


def test_download_url(linuxdeploy_local_file_plugin):
    """Local file plugins don't have a download URL."""
    # Local file plugins don't have download URL.
    with pytest.raises(RuntimeError):
        _ = linuxdeploy_local_file_plugin.download_url
