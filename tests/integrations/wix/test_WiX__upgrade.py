import os
from unittest.mock import MagicMock

import pytest

from briefcase.exceptions import (
    BriefcaseCommandError,
    MissingToolError,
    NetworkFailure,
    NonManagedToolError,
)
from briefcase.integrations.wix import WIX_DOWNLOAD_URL, WiX


def test_non_managed_install(mock_tools, tmp_path, capsys):
    """If the WiX install points to a non-managed install, no upgrade is
    attempted."""

    # Make the installation point to somewhere else.
    wix = WiX(mock_tools, wix_home=tmp_path / "other-WiX")

    # Attempt an upgrade. This will fail because the install is non-managed
    with pytest.raises(NonManagedToolError):
        wix.upgrade()

    # No download was attempted
    assert mock_tools.download.file.call_count == 0


def test_non_existing_wix_install(mock_tools, tmp_path):
    """If there's no existing managed WiX install, upgrading is an error."""
    # Create an SDK wrapper around a non-existing managed install
    wix = WiX(mock_tools, wix_home=tmp_path / "tools" / "wix")

    with pytest.raises(MissingToolError):
        wix.upgrade()

    # No download was attempted
    assert mock_tools.download.file.call_count == 0


def test_existing_wix_install(mock_tools, tmp_path):
    """If there's an existing managed WiX install, it is deleted and
    redownloaded."""
    # Create a mock of a previously installed WiX version.
    wix_path = tmp_path / "tools" / "wix"
    wix_path.mkdir(parents=True)
    (wix_path / "heat.exe").touch()
    (wix_path / "light.exe").touch()
    (wix_path / "candle.exe").touch()

    # Mock the download
    wix_path = tmp_path / "tools" / "wix"

    wix_zip_path = os.fsdecode(tmp_path / "tools" / "wix.zip")
    # Consider to remove if block when we drop py3.7 support, only keep statements from else.
    # MagicMock below py3.8 doesn't have __fspath__ attribute.
    wix_zip = MagicMock()
    wix_zip.__fspath__.return_value = wix_zip_path

    mock_tools.download.file.return_value = wix_zip

    # Create an SDK wrapper
    wix = WiX(mock_tools, wix_home=wix_path, bin_install=True)

    # Attempt an upgrade.
    wix.upgrade()

    # The old version has been deleted
    mock_tools.shutil.rmtree.assert_called_with(wix_path)

    # A download was initiated
    mock_tools.download.file.assert_called_with(
        url=WIX_DOWNLOAD_URL,
        download_path=tmp_path / "tools",
        role="WiX",
    )

    # The download was unpacked
    # TODO: Py3.6 compatibility; os.fsdecode not required in Py3.7
    mock_tools.shutil.unpack_archive.assert_called_with(
        os.fsdecode(wix_zip_path), extract_dir=os.fsdecode(wix_path)
    )

    # The zip file was removed
    wix_zip.unlink.assert_called_with()


def test_download_fail(mock_tools, tmp_path):
    """If the download doesn't complete, the upgrade fails."""
    # Create a mock of a previously installed WiX version.
    wix_path = tmp_path / "tools" / "wix"
    wix_path.mkdir(parents=True)
    (wix_path / "heat.exe").touch()
    (wix_path / "light.exe").touch()
    (wix_path / "candle.exe").touch()

    # Mock the download failure
    mock_tools.download.file.side_effect = NetworkFailure("mock")

    # Create an SDK wrapper
    wix = WiX(mock_tools, wix_home=wix_path, bin_install=True)

    # Upgrade the install. This will trigger a download that will fail
    with pytest.raises(NetworkFailure, match="Unable to mock"):
        wix.upgrade()

    # A download was initiated
    mock_tools.download.file.assert_called_with(
        url=WIX_DOWNLOAD_URL,
        download_path=tmp_path / "tools",
        role="WiX",
    )

    # ... but the unpack didn't happen
    assert mock_tools.shutil.unpack_archive.call_count == 0


def test_unpack_fail(mock_tools, tmp_path):
    """If the download archive is corrupted, the validator fails."""
    # Create a mock of a previously installed WiX version.
    wix_path = tmp_path / "tools" / "wix"
    wix_path.mkdir(parents=True)
    (wix_path / "heat.exe").touch()
    (wix_path / "light.exe").touch()
    (wix_path / "candle.exe").touch()

    # Mock the download
    wix_zip_path = os.fsdecode(tmp_path / "tools" / "wix.zip")
    # Consider to remove if block when we drop py3.7 support, only keep statements from else.
    # MagicMock below py3.8 doesn't have __fspath__ attribute.
    wix_zip = MagicMock()
    wix_zip.__fspath__.return_value = wix_zip_path

    mock_tools.download.file.return_value = wix_zip

    # Mock an unpack failure
    mock_tools.shutil.unpack_archive.side_effect = EOFError

    # Create an SDK wrapper
    wix = WiX(mock_tools, wix_home=wix_path, bin_install=True)

    # Upgrade the install. This will trigger a download,
    # but the unpack will fail.
    with pytest.raises(BriefcaseCommandError):
        wix.upgrade()

    # A download was initiated
    mock_tools.download.file.assert_called_with(
        url=WIX_DOWNLOAD_URL,
        download_path=tmp_path / "tools",
        role="WiX",
    )

    # The download was unpacked.
    # TODO: Py3.6 compatibility; os.fsdecode not required in Py3.7
    mock_tools.shutil.unpack_archive.assert_called_with(
        os.fsdecode(wix_zip_path), extract_dir=os.fsdecode(wix_path)
    )

    # The zip file was not removed
    assert wix_zip.unlink.call_count == 0
