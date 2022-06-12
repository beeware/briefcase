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


def test_verify_exists(mock_command, tmp_path):
    """If linuxdeploy gtk plugin already exists, verify doesn't download."""
    plugin_path = tmp_path / "tools" / "linuxdeploy-plugin-gtk.sh"

    # Mock the existence of an install
    plugin_path.touch()

    # Create a linuxdeploy wrapper by verification
    linuxdeploy_gtk_plugin = LinuxDeployGtkPlugin.verify(mock_command)

    # No download occured
    assert mock_command.download_url.call_count == 0
    assert mock_command.os.chmod.call_count == 0

    # The build command retains the path to the downloaded file.
    assert linuxdeploy_gtk_plugin.file_path == plugin_path


def test_verify_does_not_exist_dont_install(mock_command, tmp_path):
    """If linuxdeploy gtk plugin doesn't exist, and install=False, it is *not*
    downloaded."""
    # Mock a successful download
    mock_command.download_url.return_value = "new-downloaded-file"

    # True to create a linuxdeploy wrapper by verification.
    # This will fail because it doesn't exist, but installation was disabled.
    with pytest.raises(MissingToolError):
        LinuxDeployGtkPlugin.verify(mock_command, install=False)

    # No download occured
    assert mock_command.download_url.call_count == 0
    assert mock_command.os.chmod.call_count == 0


def test_verify_does_not_exist(mock_command, tmp_path):
    """If linuxdeploy gtk plugin doesn't exist, it is downloaded."""
    plugin_path = tmp_path / "tools" / "linuxdeploy-plugin-gtk.sh"

    # Mock a successful download
    def side_effect_create_mock_plugin(*args, **kwargs):
        plugin_path.touch()
        return "new-downloaded-file"

    mock_command.download_url.side_effect = side_effect_create_mock_plugin

    # Create a linuxdeploy gtk plugin wrapper
    linuxdeploy = LinuxDeployGtkPlugin.verify(mock_command)

    # A download is invoked
    mock_command.download_url.assert_called_with(
        url="https://raw.githubusercontent.com/linuxdeploy/linuxdeploy-plugin-gtk/"
        "master/linuxdeploy-plugin-gtk.sh",
        download_path=tmp_path / "tools",
    )
    # The downloaded file will be made executable
    mock_command.os.chmod.assert_called_with("new-downloaded-file", 0o755)

    # The build command retains the path to the downloaded file.
    assert linuxdeploy.file_path == plugin_path


def test_verify_linuxdeploy_gtk_download_failure(mock_command, tmp_path):
    """If linuxdeploy doesn't exist, but a download failure occurs, an error is
    raised."""
    mock_command.download_url.side_effect = requests_exceptions.ConnectionError

    with pytest.raises(NetworkFailure):
        LinuxDeployGtkPlugin.verify(mock_command)

    # A download was invoked
    mock_command.download_url.assert_called_with(
        url="https://raw.githubusercontent.com/linuxdeploy/linuxdeploy-plugin-gtk/"
        "master/linuxdeploy-plugin-gtk.sh",
        download_path=tmp_path / "tools",
    )
