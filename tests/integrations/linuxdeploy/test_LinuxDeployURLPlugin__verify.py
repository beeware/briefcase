import pytest

from briefcase.exceptions import BriefcaseCommandError, NetworkFailure
from briefcase.integrations.linuxdeploy import LinuxDeployURLPlugin

from .utils import side_effect_create_mock_appimage


def test_verify(mock_tools, tmp_path):
    """URL plugins will be downloaded."""
    # Mock a successful download
    mock_tools.download.file.side_effect = side_effect_create_mock_appimage(
        tmp_path
        / "tools"
        / "linuxdeploy_plugins"
        / "sometool"
        / "f3355f8e631ffc1abbb7afd37b36315f7846182ca2276c481fb9a43a7f4d239f"
        / "linuxdeploy-plugin-sometool-wonky.AppImage"
    )

    LinuxDeployURLPlugin.verify(
        mock_tools,
        url="https://example.com/path/to/linuxdeploy-plugin-sometool-wonky.AppImage",
    )

    mock_tools.download.file.assert_called_with(
        url="https://example.com/path/to/linuxdeploy-plugin-sometool-wonky.AppImage",
        download_path=tmp_path
        / "tools"
        / "linuxdeploy_plugins"
        / "sometool"
        / "f3355f8e631ffc1abbb7afd37b36315f7846182ca2276c481fb9a43a7f4d239f",
        role="user-provided linuxdeploy plugin from URL",
    )


def test_download_failure(mock_tools, tmp_path):
    """A failure downloading a custom URL plugin raises an error."""

    # Mock a successful download
    mock_tools.download.file.side_effect = NetworkFailure("mock")

    url = "https://example.com/path/to/linuxdeploy-plugin-sometool-wonky.AppImage"

    with pytest.raises(NetworkFailure, match="Unable to mock"):
        LinuxDeployURLPlugin.verify(mock_tools, url=url)

    # A download was invoked
    mock_tools.download.file.assert_called_with(
        url=url,
        download_path=mock_tools.base_path
        / "linuxdeploy_plugins"
        / "sometool"
        / "f3355f8e631ffc1abbb7afd37b36315f7846182ca2276c481fb9a43a7f4d239f",
        role="user-provided linuxdeploy plugin from URL",
    )


def test_invalid_plugin_name(mock_tools, tmp_path):
    """If the URL filename doesn't match the pattern of a linuxdeploy plugin,
    an error is raised."""

    with pytest.raises(BriefcaseCommandError):
        LinuxDeployURLPlugin.verify(
            mock_tools,
            url="https://example.com/path/to/not-a-plugin.exe",
        )
