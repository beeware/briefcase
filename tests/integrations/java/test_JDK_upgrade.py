import os
import shutil
from unittest.mock import MagicMock

import pytest

from briefcase.exceptions import (
    BriefcaseCommandError,
    MissingToolError,
    NetworkFailure,
    NonManagedToolError,
)
from briefcase.integrations.base import ToolCache
from briefcase.integrations.java import JDK


@pytest.fixture
def mock_tools(mock_tools) -> ToolCache:
    mock_tools.host_os = "Linux"
    return mock_tools


def test_non_managed_install(mock_tools, tmp_path, capsys):
    """If the Java install points to a non-managed install, no upgrade is
    attempted."""

    # Make the installation point to somewhere else.
    jdk = JDK(mock_tools, java_home=tmp_path / "other-jdk")

    # Attempt an upgrade. This will fail because the install is non-managed
    with pytest.raises(NonManagedToolError):
        jdk.upgrade()

    # No download was attempted
    assert mock_tools.download.file.call_count == 0


def test_non_existing_install(mock_tools, tmp_path):
    """If there's no existing managed JDK install, upgrading is an error."""
    # Create an SDK wrapper around a non-existing managed install
    jdk = JDK(mock_tools, java_home=tmp_path / "tools" / "java")

    with pytest.raises(MissingToolError):
        jdk.upgrade()

    # No download was attempted
    assert mock_tools.download.file.call_count == 0


def test_existing_install(mock_tools, tmp_path):
    """If there's an existing managed JDK install, it is deleted and
    redownloaded."""
    # Create a mock of a previously installed Java version.
    java_home = tmp_path / "tools" / "java"
    (java_home / "bin").mkdir(parents=True)

    # We actually need to delete the original java install
    def rmtree(path):
        shutil.rmtree(path)

    mock_tools.shutil.rmtree.side_effect = rmtree

    # Mock the cached download path.
    # Consider to remove if block when we drop py3.7 support, only keep statements from else.
    # MagicMock below py3.8 doesn't have __fspath__ attribute.
    archive = MagicMock()
    archive.__fspath__.return_value = "/path/to/download.zip"
    mock_tools.download.file.return_value = archive

    # Create a directory to make it look like Java was downloaded and unpacked.
    (tmp_path / "tools" / "jdk8u242-b08").mkdir(parents=True)

    # Create an SDK wrapper
    jdk = JDK(mock_tools, java_home=java_home)

    # Attempt an upgrade.
    jdk.upgrade()

    # The old version has been deleted
    mock_tools.shutil.rmtree.assert_called_with(java_home)

    # A download was initiated
    mock_tools.download.file.assert_called_with(
        url="https://github.com/AdoptOpenJDK/openjdk8-binaries/releases/download/"
        "jdk8u242-b08/OpenJDK8U-jdk_x64_linux_hotspot_8u242b08.tar.gz",
        download_path=tmp_path / "tools",
        role="Java 8 JDK",
    )

    # The archive was unpacked.
    # TODO: Py3.6 compatibility; os.fsdecode not required in Py3.7
    mock_tools.shutil.unpack_archive.assert_called_with(
        "/path/to/download.zip", extract_dir=os.fsdecode(tmp_path / "tools")
    )
    # The original archive was deleted
    archive.unlink.assert_called_once_with()


def test_macOS_existing_install(mock_tools, tmp_path):
    """If there's an existing managed macOS JDK install, it is deleted and
    redownloaded."""
    # Force mocking on macOS
    mock_tools.host_os = "Darwin"

    # Create a mock of a previously installed Java version.
    java_home = tmp_path / "tools" / "java" / "Contents" / "Home"
    (java_home / "bin").mkdir(parents=True)

    # We actually need to delete the original java install
    def rmtree(path):
        shutil.rmtree(path)

    mock_tools.shutil.rmtree.side_effect = rmtree

    # Mock the cached download path.
    # Consider to remove if block when we drop py3.7 support, only keep statements from else.
    # MagicMock below py3.8 doesn't have __fspath__ attribute.
    archive = MagicMock()
    archive.__fspath__.return_value = "/path/to/download.zip"
    mock_tools.download.file.return_value = archive

    # Create a directory to make it look like Java was downloaded and unpacked.
    (tmp_path / "tools" / "jdk8u242-b08").mkdir(parents=True)

    # Create an SDK wrapper
    jdk = JDK(mock_tools, java_home=java_home)

    # Attempt an upgrade.
    jdk.upgrade()

    # The old version has been deleted
    mock_tools.shutil.rmtree.assert_called_with(tmp_path / "tools" / "java")

    # A download was initiated
    mock_tools.download.file.assert_called_with(
        url="https://github.com/AdoptOpenJDK/openjdk8-binaries/releases/download/"
        "jdk8u242-b08/OpenJDK8U-jdk_x64_mac_hotspot_8u242b08.tar.gz",
        download_path=tmp_path / "tools",
        role="Java 8 JDK",
    )

    # The archive was unpacked.
    # TODO: Py3.6 compatibility; os.fsdecode not required in Py3.7
    mock_tools.shutil.unpack_archive.assert_called_with(
        "/path/to/download.zip", extract_dir=os.fsdecode(tmp_path / "tools")
    )
    # The original archive was deleted
    archive.unlink.assert_called_once_with()


def test_download_fail(mock_tools, tmp_path):
    """If there's an existing managed JDK install, it is deleted and
    redownloaded."""
    # Create a mock of a previously installed Java version.
    java_home = tmp_path / "tools" / "java"
    (java_home / "bin").mkdir(parents=True)

    # We actually need to delete the original java install
    def rmtree(path):
        shutil.rmtree(path)

    mock_tools.shutil.rmtree.side_effect = rmtree

    # Mock a failure on download
    mock_tools.download.file.side_effect = NetworkFailure("mock")

    # Create an SDK wrapper
    jdk = JDK(mock_tools, java_home=java_home)

    # Attempt an upgrade. This will fail along with the download
    with pytest.raises(NetworkFailure, match="Unable to mock"):
        jdk.upgrade()

    # The old version has been deleted
    mock_tools.shutil.rmtree.assert_called_with(java_home)

    # A download was initiated
    mock_tools.download.file.assert_called_with(
        url="https://github.com/AdoptOpenJDK/openjdk8-binaries/releases/download/"
        "jdk8u242-b08/OpenJDK8U-jdk_x64_linux_hotspot_8u242b08.tar.gz",
        download_path=tmp_path / "tools",
        role="Java 8 JDK",
    )

    # No attempt was made to unpack the archive
    assert mock_tools.shutil.unpack_archive.call_count == 0


def test_unpack_fail(mock_tools, tmp_path):
    """If there's an existing managed JDK install, it is deleted and
    redownloaded."""
    # Create a mock of a previously installed Java version.
    java_home = tmp_path / "tools" / "java"
    (java_home / "bin").mkdir(parents=True)

    # We actually need to delete the original java install
    def rmtree(path):
        shutil.rmtree(path)

    mock_tools.shutil.rmtree.side_effect = rmtree

    # Mock the cached download path
    # Consider to remove if block when we drop py3.7 support, only keep statements from else.
    # MagicMock below py3.8 doesn't have __fspath__ attribute.
    archive = MagicMock()
    archive.__fspath__.return_value = "/path/to/download.zip"
    mock_tools.download.file.return_value = archive

    # Mock an unpack failure due to an invalid archive
    mock_tools.shutil.unpack_archive.side_effect = shutil.ReadError

    # Create an SDK wrapper
    jdk = JDK(mock_tools, java_home=java_home)

    # Attempt an upgrade. This will fail.
    with pytest.raises(BriefcaseCommandError):
        jdk.upgrade()

    # The old version has been deleted
    mock_tools.shutil.rmtree.assert_called_with(java_home)

    # A download was initiated
    mock_tools.download.file.assert_called_with(
        url="https://github.com/AdoptOpenJDK/openjdk8-binaries/releases/download/"
        "jdk8u242-b08/OpenJDK8U-jdk_x64_linux_hotspot_8u242b08.tar.gz",
        download_path=tmp_path / "tools",
        role="Java 8 JDK",
    )

    # The archive was unpacked.
    # TODO: Py3.6 compatibility; os.fsdecode not required in Py3.7
    mock_tools.shutil.unpack_archive.assert_called_with(
        "/path/to/download.zip", extract_dir=os.fsdecode(tmp_path / "tools")
    )
    # The original archive was not deleted
    assert archive.unlink.call_count == 0
