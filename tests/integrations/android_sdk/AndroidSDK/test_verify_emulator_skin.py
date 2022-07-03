import sys
from unittest.mock import MagicMock

import pytest
from requests import exceptions as requests_exceptions

from briefcase.exceptions import BriefcaseCommandError, NetworkFailure
from tests.utils import FsPathMock


def test_existing_skin(mock_sdk):
    """If the skin already exists, don't attempt to download it again."""
    # Mock the existence of a system image
    (mock_sdk.root_path / "skins" / "pixel_X").mkdir(parents=True)

    # Verify the system image that we already have
    mock_sdk.verify_emulator_skin("pixel_X")

    # download_url was *not* called.
    mock_sdk.command.download_url.assert_not_called()


def test_new_skin(mock_sdk):
    """If the skin doesn't exist, an attempt is made to download it."""
    # MagicMock below py3.8 doesn't has __fspath__ attribute.
    # Remove if block when we drop py3.7 support.
    if sys.version_info < (3, 8):
        skin_tgz_path = FsPathMock("/path/to/skin.tgz")
    else:
        skin_tgz_path = MagicMock()
        skin_tgz_path.__fspath__.return_value = "/path/to/skin.tgz"
    mock_sdk.command.download_url.return_value = skin_tgz_path

    # Verify the skin, triggering a download
    mock_sdk.verify_emulator_skin("pixel_X")

    # Skin was downloaded
    mock_sdk.command.download_url.assert_called_once_with(
        url="https://android.googlesource.com/platform/tools/adt/idea/"
        "+archive/refs/heads/mirror-goog-studio-main/"
        "artwork/resources/device-art-resources/pixel_X.tar.gz",
        download_path=mock_sdk.root_path,
    )

    # Skin is unpacked.
    mock_sdk.command.shutil.unpack_archive.assert_called_once_with(
        skin_tgz_path, extract_dir=mock_sdk.root_path / "skins" / "pixel_X"
    )

    # Original file was deleted.
    skin_tgz_path.unlink.assert_called_once_with()


def test_skin_download_failure(mock_sdk, tmp_path):
    """If the skin download fails, an error is raised."""
    # MagicMock below py3.8 doesn't has __fspath__ attribute.
    # Remove if block when we drop py3.7 support.
    if sys.version_info < (3, 8):
        skin_tgz_path = FsPathMock("/path/to/skin.tgz")
    else:
        skin_tgz_path = MagicMock()
        skin_tgz_path.__fspath__.return_value = "/path/to/skin.tgz"
    mock_sdk.command.download_url.return_value = skin_tgz_path

    # Mock a failure downloading the skin
    mock_sdk.command.download_url.side_effect = requests_exceptions.ConnectionError

    # Verify the skin, triggering a download
    with pytest.raises(NetworkFailure):
        mock_sdk.verify_emulator_skin("pixel_X")

    # An attempt was made to download the skin
    mock_sdk.command.download_url.assert_called_once_with(
        url="https://android.googlesource.com/platform/tools/adt/idea/"
        "+archive/refs/heads/mirror-goog-studio-main/"
        "artwork/resources/device-art-resources/pixel_X.tar.gz",
        download_path=mock_sdk.root_path,
    )

    # Skin wasn't downloaded, so it wasn't unpacked
    assert mock_sdk.command.shutil.unpack_archive.call_count == 0


def test_unpack_failure(mock_sdk, tmp_path):
    """If the download is corrupted and unpacking fails, an error is raised."""
    # Mock the result of the download of a skin
    # Consider to remove if block when we drop py3.7 support, only keep statements from else.
    # MagicMock below py3.8 doesn't has __fspath__ attribute.
    if sys.version_info < (3, 8):
        skin_tgz_path = FsPathMock("/path/to/skin.tgz")
    else:
        skin_tgz_path = MagicMock()
        skin_tgz_path.__fspath__.return_value = "/path/to/skin.tgz"
    mock_sdk.command.download_url.return_value = skin_tgz_path

    # Mock a failure unpacking the skin
    mock_sdk.command.shutil.unpack_archive.side_effect = EOFError

    # Verify the skin, triggering a download
    with pytest.raises(
        BriefcaseCommandError,
        match=r"Unable to unpack pixel_X device skin.",
    ):
        mock_sdk.verify_emulator_skin("pixel_X")

    # Skin was downloaded
    mock_sdk.command.download_url.assert_called_once_with(
        url="https://android.googlesource.com/platform/tools/adt/idea/"
        "+archive/refs/heads/mirror-goog-studio-main/"
        "artwork/resources/device-art-resources/pixel_X.tar.gz",
        download_path=mock_sdk.root_path,
    )

    # An attempt to unpack the skin was made.
    mock_sdk.command.shutil.unpack_archive.assert_called_once_with(
        skin_tgz_path, extract_dir=mock_sdk.root_path / "skins" / "pixel_X"
    )

    # Original file wasn't deleted.
    assert skin_tgz_path.unlink.call_count == 0
