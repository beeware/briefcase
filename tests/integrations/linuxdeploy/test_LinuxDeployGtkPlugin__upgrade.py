from unittest.mock import MagicMock

import pytest
from requests import exceptions as requests_exceptions

from briefcase.exceptions import MissingToolError, NetworkFailure
from briefcase.integrations.linuxdeploy import LinuxDeployGtkPlugin


@pytest.fixture
def mock_command(tmp_path):
    command = MagicMock()
    command.tools_path = tmp_path / "tools"
    command.tools_path.mkdir()

    return command


def test_upgrade_exists(mock_command, tmp_path):
    """If linuxdeploy gtk already exists, upgrading deletes first."""
    plugin_path = tmp_path / "tools" / "linuxdeploy-plugin-gtk.sh"

    # Mock already installed
    plugin_path.touch()

    # Mock a successful download
    def side_effect_create_mock_plugin(*args, **kwargs):
        plugin_path.touch()
        return "new-downloaded-file"

    mock_command.download_url.side_effect = side_effect_create_mock_plugin

    # Create a linuxdeploy gtk wrapper, then upgrade it
    linuxdeploy_gtk_plugin = LinuxDeployGtkPlugin(mock_command)
    linuxdeploy_gtk_plugin.upgrade()

    # The mock file should exist as the upgraded version
    assert plugin_path.exists()

    # A download is invoked
    mock_command.download_url.assert_called_with(
        url="https://raw.githubusercontent.com/linuxdeploy/linuxdeploy-plugin-gtk/"
        "master/linuxdeploy-plugin-gtk.sh",
        download_path=tmp_path / "tools",
    )
    # The downloaded file will be made executable
    mock_command.os.chmod.assert_called_with("new-downloaded-file", 0o755)


def test_upgrade_does_not_exist(mock_command, tmp_path):
    """If linuxdeploy gtk plugin doesn't already exist, upgrading is an
    error."""
    # Create a linuxdeploy gtk plugin wrapper, then upgrade it
    linuxdeploy_gtk_plugin = LinuxDeployGtkPlugin(mock_command)
    with pytest.raises(MissingToolError):
        linuxdeploy_gtk_plugin.upgrade()

    # The tool wasn't already installed, so an error is raised.
    assert mock_command.download_url.call_count == 0


def test_upgrade_linuxdeploy_gtk_download_failure(mock_command, tmp_path):
    """If linuxdeploy gtk doesn't exist, but a download failure occurs, an
    error is raised."""
    # Mock the existence of an install
    plugin_path = tmp_path / "tools" / "linuxdeploy-plugin-gtk.sh"
    plugin_path.touch()

    mock_command.download_url.side_effect = requests_exceptions.ConnectionError

    # Create a linuxdeploy gtk wrapper, then upgrade it.
    # The upgrade will fail
    linuxdeploy_gtk_path = LinuxDeployGtkPlugin(mock_command)
    with pytest.raises(NetworkFailure):
        linuxdeploy_gtk_path.upgrade()

    # The mock file will be deleted
    assert not plugin_path.exists()

    # A download was invoked
    mock_command.download_url.assert_called_with(
        url="https://raw.githubusercontent.com/linuxdeploy/linuxdeploy-plugin-gtk/"
        "master/linuxdeploy-plugin-gtk.sh",
        download_path=tmp_path / "tools",
    )
