import pytest

from briefcase.exceptions import BriefcaseCommandError, UnsupportedHostError
from briefcase.integrations.linuxdeploy import LinuxDeployLocalFilePlugin

from .utils import create_mock_appimage


@pytest.mark.parametrize("host_os", ["Windows", "wonky"])
def test_unsupported_os(mock_tools, host_os):
    """When host OS is not supported, an error is raised."""
    mock_tools.host_os = host_os

    with pytest.raises(
        UnsupportedHostError,
        match=f"{LinuxDeployLocalFilePlugin.name} is not supported on {host_os}",
    ):
        LinuxDeployLocalFilePlugin.verify(mock_tools)


def test_verify(mock_tools, tmp_path):
    """Local file plugins are installed by copying."""
    plugin_path = tmp_path / "path/to/linuxdeploy-plugin-custom.sh"
    create_mock_appimage(plugin_path)

    LinuxDeployLocalFilePlugin.verify(
        mock_tools,
        plugin_path=plugin_path,
        bundle_path=tmp_path / "bundle",
    )

    # The plugin is copied into place
    assert (tmp_path / "bundle/linuxdeploy-plugin-custom.sh").exists()


def test_bad_path(mock_tools, tmp_path):
    """If the plugin file path is invalid, an error is raised."""
    plugin_path = tmp_path / "path/to/linuxdeploy-plugin-custom.sh"

    with pytest.raises(
        BriefcaseCommandError,
        match=r"Could not locate linuxdeploy plugin ",
    ):
        LinuxDeployLocalFilePlugin.verify(
            mock_tools,
            plugin_path=plugin_path,
            bundle_path=tmp_path / "bundle",
        )


def test_non_plugin(mock_tools, tmp_path):
    """If the plugin file path exists, but the filename doesn't match the pattern of a
    linuxdeploy plugin, an error is raised."""
    plugin_path = tmp_path / "path/to/not-a-plugin.exe"
    create_mock_appimage(plugin_path)

    with pytest.raises(
        BriefcaseCommandError,
        match=r"not-a-plugin.exe is not a linuxdeploy plugin",
    ):
        LinuxDeployLocalFilePlugin.verify(
            mock_tools,
            plugin_path=plugin_path,
            bundle_path=tmp_path / "bundle",
        )
