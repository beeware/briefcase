import pytest

from briefcase.exceptions import MissingToolError, NetworkFailure
from briefcase.integrations.linuxdeploy import LinuxDeployBase
from tests.integrations.linuxdeploy.utils import side_effect_create_mock_appimage


@pytest.fixture
def linuxdeploy(mock_tools, tmp_path):
    class LinuxDeployDummy(LinuxDeployBase):
        name = "dummy-plugin"
        full_name = "Dummy plugin"

        @property
        def file_name(self):
            return "linuxdeploy-dummy-wonky.AppImage"

        @property
        def download_url(self):
            return "https://example.com/path/to/linuxdeploy-dummy-wonky.AppImage"

        @property
        def file_path(self):
            return tmp_path / "plugin"

    return LinuxDeployDummy(mock_tools)


def test_upgrade_exists(linuxdeploy, mock_tools, tmp_path):
    """If linuxdeploy already exists, upgrading deletes first."""
    appimage_path = tmp_path / "plugin" / "linuxdeploy-dummy-wonky.AppImage"

    # Mock the existence of an install
    appimage_path.parent.mkdir(parents=True)
    appimage_path.touch()

    # Mock a successful download
    mock_tools.download.file.side_effect = side_effect_create_mock_appimage(
        appimage_path
    )

    # Create a linuxdeploy wrapper, then upgrade it
    linuxdeploy.upgrade()

    # The mock file should exist as the upgraded version
    assert appimage_path.exists()

    # A download is invoked
    mock_tools.download.file.assert_called_with(
        url="https://example.com/path/to/linuxdeploy-dummy-wonky.AppImage",
        download_path=tmp_path / "plugin",
        role="Dummy plugin",
    )
    # The downloaded file will be made executable
    mock_tools.os.chmod.assert_called_with(appimage_path, 0o755)


def test_upgrade_does_not_exist(linuxdeploy, mock_tools):
    """If linuxdeploy doesn't already exist, upgrading is an error."""
    # Create a linuxdeploy wrapper, then upgrade it
    with pytest.raises(MissingToolError):
        linuxdeploy.upgrade()

    # The tool wasn't already installed, so an error is raised.
    assert mock_tools.download.file.call_count == 0


def test_upgrade_linuxdeploy_download_failure(linuxdeploy, mock_tools, tmp_path):
    """If linuxdeploy doesn't exist, but a download failure occurs, an error is
    raised."""
    # Mock the existence of an install
    appimage_path = tmp_path / "plugin" / "linuxdeploy-dummy-wonky.AppImage"
    appimage_path.parent.mkdir(parents=True)
    appimage_path.touch()

    mock_tools.download.file.side_effect = NetworkFailure("mock")

    # Updated the linuxdeploy wrapper; the upgrade will fail
    with pytest.raises(NetworkFailure, match="Unable to mock"):
        linuxdeploy.upgrade()

    # The mock file will be deleted
    assert not appimage_path.exists()

    # A download was invoked
    mock_tools.download.file.assert_called_with(
        url="https://example.com/path/to/linuxdeploy-dummy-wonky.AppImage",
        download_path=tmp_path / "plugin",
        role="Dummy plugin",
    )
