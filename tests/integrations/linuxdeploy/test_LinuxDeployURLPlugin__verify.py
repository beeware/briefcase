import pytest
from requests import exceptions as requests_exceptions

from briefcase.exceptions import BriefcaseCommandError, NetworkFailure
from briefcase.integrations.linuxdeploy import LinuxDeployURLPlugin

from .utils import side_effect_create_mock_appimage


def test_verify(mock_command, tmp_path):
    """URL plugins will be downloaded."""
    # Mock a successful download
    mock_command.download_url.side_effect = side_effect_create_mock_appimage(
        tmp_path
        / "tools"
        / "linuxdeploy_plugins"
        / "sometool"
        / "c217c55393ac3e43f7d558294bae580052b69764b423cc73fa57a47c65455467"
        / "linuxdeploy-plugin-sometool-wonky.AppImage"
    )

    LinuxDeployURLPlugin.verify(
        mock_command,
        url="https://example.com/path/to/linuxdeploy-plugin-sometool-wonky.AppImage",
    )

    mock_command.download_url.assert_called_with(
        url="https://example.com/path/to/linuxdeploy-plugin-sometool-wonky.AppImage",
        download_path=tmp_path
        / "tools"
        / "linuxdeploy_plugins"
        / "sometool"
        / "c217c55393ac3e43f7d558294bae580052b69764b423cc73fa57a47c65455467",
    )


def test_download_failure(mock_command, tmp_path):
    """A failure downloading a custom URL plugin raises an error."""

    # Mock a successful download
    mock_command.download_url.side_effect = requests_exceptions.ConnectionError

    with pytest.raises(NetworkFailure):
        LinuxDeployURLPlugin.verify(
            mock_command,
            url="https://example.com/path/to/linuxdeploy-plugin-sometool-wonky.AppImage",
        )


def test_invalid_plugin_name(mock_command, tmp_path):
    """If the URL filename doesn't match the pattern of a linuxdeploy plugin,
    an error is raised."""

    with pytest.raises(BriefcaseCommandError):
        LinuxDeployURLPlugin.verify(
            mock_command,
            url="https://example.com/path/to/not-a-plugin.exe",
        )
