import pytest

from briefcase.exceptions import MissingToolError, NetworkFailure
from briefcase.integrations.rcedit import RCEdit


def test_upgrade_exists(mock_tools, tmp_path):
    """If rcedit already exists, upgrading deletes first."""
    rcedit_path = tmp_path / "tools" / "rcedit-x64.exe"

    # Mock the existence of an install
    rcedit_path.touch()

    # Mock a successful download
    def side_effect_create_mock_appimage(*args, **kwargs):
        rcedit_path.touch()
        return "new-downloaded-file"

    mock_tools.download.file.side_effect = side_effect_create_mock_appimage

    # Create a rcedit wrapper, then upgrade it
    rcedit = RCEdit(mock_tools)
    rcedit.upgrade()

    # The mock file should exist as the upgraded version
    assert rcedit_path.exists()

    # A download is invoked
    mock_tools.download.file.assert_called_with(
        url="https://github.com/electron/rcedit/"
        "releases/download/v1.1.1/rcedit-x64.exe",
        download_path=tmp_path / "tools",
        role="RCEdit",
    )


def test_upgrade_does_not_exist(mock_tools, tmp_path):
    """If rcedit doesn't already exist, upgrading is an error."""
    # Create a rcedit wrapper, then upgrade it
    rcedit = RCEdit(mock_tools)
    with pytest.raises(MissingToolError):
        rcedit.upgrade()

    # The tool wasn't already installed, so an error is raised.
    assert mock_tools.download.file.call_count == 0


def test_upgrade_rcedit_download_failure(mock_tools, tmp_path):
    """If rcedit doesn't exist, but a download failure occurs, an error is
    raised."""
    # Mock the existence of an install
    rcedit_path = tmp_path / "tools" / "rcedit-x64.exe"
    rcedit_path.touch()

    mock_tools.download.file.side_effect = NetworkFailure("mock")

    # Create a rcedit wrapper, then upgrade it.
    # The upgrade will fail
    rcedit = RCEdit(mock_tools)
    with pytest.raises(NetworkFailure, match="Unable to mock"):
        rcedit.upgrade()

    # The mock file will be deleted
    assert not rcedit_path.exists()

    # A download was invoked
    mock_tools.download.file.assert_called_with(
        url="https://github.com/electron/rcedit/"
        "releases/download/v1.1.1/rcedit-x64.exe",
        download_path=tmp_path / "tools",
        role="RCEdit",
    )
