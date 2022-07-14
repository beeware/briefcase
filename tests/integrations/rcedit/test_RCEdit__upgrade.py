from unittest.mock import MagicMock

import pytest
from requests import exceptions as requests_exceptions

from briefcase.exceptions import MissingToolError, NetworkFailure
from briefcase.integrations.rcedit import RCEdit


@pytest.fixture
def mock_command(tmp_path):
    command = MagicMock()
    command.host_arch = "wonky"
    command.tools_path = tmp_path / "tools"
    command.tools_path.mkdir()

    return command


def test_upgrade_exists(mock_command, tmp_path):
    """If rcedit already exists, upgrading deletes first."""
    rcedit_path = tmp_path / "tools" / "rcedit-x64.exe"

    # Mock the existence of an install
    rcedit_path.touch()

    # Mock a successful download
    def side_effect_create_mock_appimage(*args, **kwargs):
        rcedit_path.touch()
        return "new-downloaded-file"

    mock_command.download_url.side_effect = side_effect_create_mock_appimage

    # Create a rcedit wrapper, then upgrade it
    rcedit = RCEdit(mock_command)
    rcedit.upgrade()

    # The mock file should exist as the upgraded version
    assert rcedit_path.exists()

    # A download is invoked
    mock_command.download_url.assert_called_with(
        url="https://github.com/electron/rcedit/"
        "releases/download/v1.1.1/rcedit-x64.exe",
        download_path=tmp_path / "tools",
    )


def test_upgrade_does_not_exist(mock_command, tmp_path):
    """If rcedit doesn't already exist, upgrading is an error."""
    # Create a rcedit wrapper, then upgrade it
    rcedit = RCEdit(mock_command)
    with pytest.raises(MissingToolError):
        rcedit.upgrade()

    # The tool wasn't already installed, so an error is raised.
    assert mock_command.download_url.call_count == 0


def test_upgrade_rcedit_download_failure(mock_command, tmp_path):
    """If rcedit doesn't exist, but a download failure occurs, an error is
    raised."""
    # Mock the existence of an install
    rcedit_path = tmp_path / "tools" / "rcedit-x64.exe"
    rcedit_path.touch()

    mock_command.download_url.side_effect = requests_exceptions.ConnectionError

    # Create a rcedit wrapper, then upgrade it.
    # The upgrade will fail
    rcedit = RCEdit(mock_command)
    with pytest.raises(NetworkFailure):
        rcedit.upgrade()

    # The mock file will be deleted
    assert not rcedit_path.exists()

    # A download was invoked
    mock_command.download_url.assert_called_with(
        url="https://github.com/electron/rcedit/"
        "releases/download/v1.1.1/rcedit-x64.exe",
        download_path=tmp_path / "tools",
    )
