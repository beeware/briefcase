from pathlib import Path
from unittest.mock import MagicMock

import pytest

from briefcase.exceptions import BriefcaseCommandError, NetworkFailure


def test_existing_skin(mock_tools, android_sdk):
    """If the skin already exists, don't attempt to download it again."""
    # Mock the existence of a system image
    (android_sdk.root_path / "skins" / "pixel_X").mkdir(parents=True)

    # Verify the system image that we already have
    android_sdk.verify_emulator_skin("pixel_X")

    # download.file was *not* called.
    mock_tools.download.file.assert_not_called()


def test_new_skin(mock_tools, android_sdk):
    """If the skin doesn't exist, an attempt is made to download it."""
    # MagicMock below py3.8 doesn't have __fspath__ attribute.
    # Remove if block when we drop py3.7 support.
    skin_tgz_path = MagicMock(spec_set=Path)
    skin_tgz_path.__fspath__.return_value = "/path/to/skin.tgz"
    mock_tools.download.file.return_value = skin_tgz_path

    # Verify the skin, triggering a download
    android_sdk.verify_emulator_skin("pixel_X")

    # Skin was downloaded
    mock_tools.download.file.assert_called_once_with(
        url="https://android.googlesource.com/platform/tools/adt/idea/"
        "+archive/refs/heads/mirror-goog-studio-main/"
        "artwork/resources/device-art-resources/pixel_X.tar.gz",
        download_path=android_sdk.root_path,
        role="pixel_X device skin",
    )

    # Skin is unpacked.
    mock_tools.shutil.unpack_archive.assert_called_once_with(
        skin_tgz_path,
        extract_dir=android_sdk.root_path / "skins" / "pixel_X",
    )

    # Original file was deleted.
    skin_tgz_path.unlink.assert_called_once_with()


def test_skin_download_failure(mock_tools, android_sdk, tmp_path):
    """If the skin download fails, an error is raised."""
    # MagicMock below py3.8 doesn't have __fspath__ attribute.
    # Remove if block when we drop py3.7 support.
    skin_tgz_path = MagicMock(spec_set=Path)
    skin_tgz_path.__fspath__.return_value = "/path/to/skin.tgz"
    mock_tools.download.file.return_value = skin_tgz_path

    # Mock a failure downloading the skin
    mock_tools.download.file.side_effect = NetworkFailure("mock")

    # Verify the skin, triggering a download
    with pytest.raises(NetworkFailure, match="Unable to mock"):
        android_sdk.verify_emulator_skin("pixel_X")

    # An attempt was made to download the skin
    mock_tools.download.file.assert_called_once_with(
        url="https://android.googlesource.com/platform/tools/adt/idea/"
        "+archive/refs/heads/mirror-goog-studio-main/"
        "artwork/resources/device-art-resources/pixel_X.tar.gz",
        download_path=android_sdk.root_path,
        role="pixel_X device skin",
    )

    # Skin wasn't downloaded, so it wasn't unpacked
    assert mock_tools.shutil.unpack_archive.call_count == 0


def test_unpack_failure(mock_tools, android_sdk, tmp_path):
    """If the download is corrupted and unpacking fails, an error is raised."""
    # Mock the result of the download of a skin
    # Consider to remove if block when we drop py3.7 support, only keep statements from else.
    # MagicMock below py3.8 doesn't have __fspath__ attribute.
    skin_tgz_path = MagicMock(spec_set=Path)
    skin_tgz_path.__fspath__.return_value = "/path/to/skin.tgz"
    mock_tools.download.file.return_value = skin_tgz_path

    # Mock a failure unpacking the skin
    mock_tools.shutil.unpack_archive.side_effect = EOFError

    # Verify the skin, triggering a download
    with pytest.raises(
        BriefcaseCommandError,
        match=r"Unable to unpack pixel_X device skin.",
    ):
        android_sdk.verify_emulator_skin("pixel_X")

    # Skin was downloaded
    mock_tools.download.file.assert_called_once_with(
        url="https://android.googlesource.com/platform/tools/adt/idea/"
        "+archive/refs/heads/mirror-goog-studio-main/"
        "artwork/resources/device-art-resources/pixel_X.tar.gz",
        download_path=android_sdk.root_path,
        role="pixel_X device skin",
    )

    # An attempt to unpack the skin was made.
    mock_tools.shutil.unpack_archive.assert_called_once_with(
        skin_tgz_path,
        extract_dir=android_sdk.root_path / "skins" / "pixel_X",
    )

    # Original file wasn't deleted.
    assert skin_tgz_path.unlink.call_count == 0
