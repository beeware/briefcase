import pytest

from briefcase.exceptions import MissingToolError
from briefcase.integrations.wix import WiX


def test_non_existing_wix_install(mock_tools, tmp_path):
    """If there's no existing managed WiX install, upgrading is an error."""
    # Create an SDK wrapper around a non-existing managed install
    wix = WiX(mock_tools)

    with pytest.raises(MissingToolError):
        wix.upgrade()

    # No download was attempted
    assert mock_tools.file.download.call_count == 0


def test_wix_uninstall(mock_tools, tmp_path):
    """The uninstall method removes a managed install."""
    # Create a mock of a previously installed WiX version.
    wix_path = tmp_path / "tools/wix"
    wix_path.mkdir(parents=True)

    wix = WiX(mock_tools)
    wix.uninstall()
    mock_tools.shutil.rmtree.assert_called_once_with(wix_path)
