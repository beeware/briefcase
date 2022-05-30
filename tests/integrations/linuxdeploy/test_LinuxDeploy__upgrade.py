from unittest.mock import MagicMock

import pytest
from requests import exceptions as requests_exceptions

from briefcase.exceptions import MissingToolError, NetworkFailure
from briefcase.integrations.linuxdeploy import LinuxDeploy
from tests.integrations.linuxdeploy.utils import create_mock_appimage


@pytest.fixture
def mock_command(tmp_path):
    command = MagicMock()
    command.host_arch = "wonky"
    command.tools_path = tmp_path / "tools"
    command.tools_path.mkdir()

    return command


def test_upgrade_exists(mock_command, tmp_path):
    """If linuxdeploy already exists, upgrading deletes first."""
    appimage_path = tmp_path / "tools" / "linuxdeploy-wonky.AppImage"

    # Mock the existence of an install
    appimage_path.touch()

    # Mock a successful download
    def side_effect_create_mock_appimage(*args, **kwargs):
        create_mock_appimage(appimage_path=appimage_path)
        return "new-downloaded-file"

    mock_command.download_url.side_effect = side_effect_create_mock_appimage

    # Create a linuxdeploy wrapper, then upgrade it
    linuxdeploy = LinuxDeploy(mock_command)
    linuxdeploy.upgrade()

    # The mock file should exist as the upgraded version
    assert appimage_path.exists()

    # A download is invoked
    mock_command.download_url.assert_called_with(
        url="https://github.com/linuxdeploy/linuxdeploy/"
        "releases/download/continuous/linuxdeploy-wonky.AppImage",
        download_path=tmp_path / "tools",
    )
    # The downloaded file will be made executable
    mock_command.os.chmod.assert_called_with("new-downloaded-file", 0o755)


def test_upgrade_does_not_exist(mock_command, tmp_path):
    """If linuxdeploy doesn't already exist, upgrading is an error."""
    # Create a linuxdeploy wrapper, then upgrade it
    linuxdeploy = LinuxDeploy(mock_command)
    with pytest.raises(MissingToolError):
        linuxdeploy.upgrade()

    # The tool wasn't already installed, so an error is raised.
    assert mock_command.download_url.call_count == 0


def test_upgrade_linuxdeploy_download_failure(mock_command, tmp_path):
    """If linuxdeploy doesn't exist, but a download failure occurs, an error is
    raised."""
    # Mock the existence of an install
    appimage_path = tmp_path / "tools" / "linuxdeploy-wonky.AppImage"
    appimage_path.touch()

    mock_command.download_url.side_effect = requests_exceptions.ConnectionError

    # Create a linuxdeploy wrapper, then upgrade it.
    # The upgrade will fail
    linuxdeploy = LinuxDeploy(mock_command)
    with pytest.raises(NetworkFailure):
        linuxdeploy.upgrade()

    # The mock file will be deleted
    assert not appimage_path.exists()

    # A download was invoked
    mock_command.download_url.assert_called_with(
        url="https://github.com/linuxdeploy/linuxdeploy/"
        "releases/download/continuous/linuxdeploy-wonky.AppImage",
        download_path=tmp_path / "tools",
    )
