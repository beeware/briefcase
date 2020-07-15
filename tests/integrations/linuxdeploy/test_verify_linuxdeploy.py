from unittest.mock import MagicMock

import pytest
from requests import exceptions as requests_exceptions

from briefcase.exceptions import NetworkFailure
from briefcase.integrations.linuxdeploy import verify_linuxdeploy


@pytest.fixture
def mock_command():
    command = MagicMock()
    command.host_os = 'wonky'

    return command


def test_verify_linuxdeploy(mock_command):
    "The build process invokes verify_tools, which retrieves linuxdeploy"
    # Mock a successful download
    mock_command.download_url.return_value = 'new-downloaded-file'

    # Verify the
    linuxdeploy_appimage = verify_linuxdeploy(mock_command)

    # The downloaded file will be made executable
    mock_command.os.chmod.assert_called_with('new-downloaded-file', 0o755)

    # The build command retains the path to the downloaded file.
    assert linuxdeploy_appimage == 'new-downloaded-file'


def test_verify_linuxdeploy_download_failure(mock_command):
    "If the download of linuxdeploy fails, an error is raised"

    mock_command.download_url.side_effect = requests_exceptions.ConnectionError

    with pytest.raises(NetworkFailure):
        verify_linuxdeploy(mock_command)
