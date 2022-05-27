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


def test_verify_exists(mock_command, tmp_path):
    """If linuxdeploy already exists, verification doesn't download."""
    appimage_path = tmp_path / "tools" / "linuxdeploy-wonky.AppImage"

    # Mock the existence of an install
    appimage_path.touch()

    # Create a linuxdeploy wrapper by verification
    linuxdeploy = LinuxDeploy.verify(mock_command)

    # No download occured
    assert mock_command.download_url.call_count == 0
    assert mock_command.os.chmod.call_count == 0

    # The build command retains the path to the downloaded file.
    assert linuxdeploy.appimage_path == appimage_path


def test_verify_does_not_exist_dont_install(mock_command, tmp_path):
    """If linuxdeploy doesn't exist, and install=False, it is *not*
    downloaded."""
    # Mock a successful download
    mock_command.download_url.return_value = "new-downloaded-file"

    # True to create a linuxdeploy wrapper by verification.
    # This will fail because it doesn't exist, but installation was disabled.
    with pytest.raises(MissingToolError):
        LinuxDeploy.verify(mock_command, install=False)

    # No download occured
    assert mock_command.download_url.call_count == 0
    assert mock_command.os.chmod.call_count == 0


def test_verify_does_not_exist(mock_command, tmp_path):
    """If linuxdeploy doesn't exist, it is downloaded."""
    appimage_path = tmp_path / "tools" / "linuxdeploy-wonky.AppImage"

    # Mock a successful download
    def side_effect_create_mock_appimage(*args, **kwargs):
        create_mock_appimage(appimage_path=appimage_path)
        return "new-downloaded-file"

    mock_command.download_url.side_effect = side_effect_create_mock_appimage

    # Create a linuxdeploy wrapper by verification
    linuxdeploy = LinuxDeploy.verify(mock_command)

    # A download is invoked
    mock_command.download_url.assert_called_with(
        url="https://github.com/linuxdeploy/linuxdeploy/"
        "releases/download/continuous/linuxdeploy-wonky.AppImage",
        download_path=tmp_path / "tools",
    )
    # The downloaded file will be made executable
    mock_command.os.chmod.assert_called_with("new-downloaded-file", 0o755)

    # The build command retains the path to the downloaded file.
    assert linuxdeploy.appimage_path == appimage_path


def test_verify_linuxdeploy_download_failure(mock_command, tmp_path):
    """If linuxdeploy doesn't exist, but a download failure occurs, an error is
    raised."""
    mock_command.download_url.side_effect = requests_exceptions.ConnectionError

    with pytest.raises(NetworkFailure):
        LinuxDeploy.verify(mock_command)

    # A download was invoked
    mock_command.download_url.assert_called_with(
        url="https://github.com/linuxdeploy/linuxdeploy/"
        "releases/download/continuous/linuxdeploy-wonky.AppImage",
        download_path=tmp_path / "tools",
    )
