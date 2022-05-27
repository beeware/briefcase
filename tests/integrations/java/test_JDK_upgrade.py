import os
import shutil
import sys
from unittest.mock import MagicMock

import pytest
from requests import exceptions as requests_exceptions

from briefcase.exceptions import (
    BriefcaseCommandError,
    MissingToolError,
    NetworkFailure,
    NonManagedToolError,
)
from briefcase.integrations.java import JDK
from tests.utils import FsPathMock


@pytest.fixture
def test_command(tmp_path):
    command = MagicMock()
    command.host_os = "Linux"
    command.tools_path = tmp_path / "tools"

    return command


def test_non_managed_install(test_command, tmp_path, capsys):
    """If the Java install points to a non-managed install, no upgrade is
    attempted."""

    # Make the installation point to somewhere else.
    jdk = JDK(test_command, java_home=tmp_path / "other-jdk")

    # Attempt an upgrade. This will fail because the install is non-managed
    with pytest.raises(NonManagedToolError):
        jdk.upgrade()

    # No download was attempted
    assert test_command.download_url.call_count == 0


def test_non_existing_install(test_command, tmp_path):
    """If there's no existing managed JDK install, upgrading is an error."""
    # Create an SDK wrapper around a non-existing managed install
    jdk = JDK(test_command, java_home=tmp_path / "tools" / "java")

    with pytest.raises(MissingToolError):
        jdk.upgrade()

    # No download was attempted
    assert test_command.download_url.call_count == 0


def test_existing_install(test_command, tmp_path):
    """If there's an existing managed JDK install, it is deleted and
    redownloaded."""
    # Create a mock of a previously installed Java version.
    java_home = tmp_path / "tools" / "java"
    (java_home / "bin").mkdir(parents=True)

    # We actually need to delete the original java install
    def rmtree(path):
        shutil.rmtree(path)

    test_command.shutil.rmtree.side_effect = rmtree

    # Mock the cached download path.
    # Consider to remove if block when we drop py3.7 support, only keep statements from else.
    # MagicMock below py3.8 doesn't has __fspath__ attribute.
    if sys.version_info < (3, 8):
        archive = FsPathMock("/path/to/download.zip")
    else:
        archive = MagicMock()
        archive.__fspath__.return_value = "/path/to/download.zip"
    test_command.download_url.return_value = archive

    # Create a directory to make it look like Java was downloaded and unpacked.
    (tmp_path / "tools" / "jdk8u242-b08").mkdir(parents=True)

    # Create an SDK wrapper
    jdk = JDK(test_command, java_home=java_home)

    # Attempt an upgrade.
    jdk.upgrade()

    # The old version has been deleted
    test_command.shutil.rmtree.assert_called_with(java_home)

    # A download was initiated
    test_command.download_url.assert_called_with(
        url="https://github.com/AdoptOpenJDK/openjdk8-binaries/releases/download/"
        "jdk8u242-b08/OpenJDK8U-jdk_x64_linux_hotspot_8u242b08.tar.gz",
        download_path=tmp_path / "tools",
    )

    # The archive was unpacked.
    # TODO: Py3.6 compatibility; os.fsdecode not required in Py3.7
    test_command.shutil.unpack_archive.assert_called_with(
        "/path/to/download.zip", extract_dir=os.fsdecode(tmp_path / "tools")
    )
    # The original archive was deleted
    archive.unlink.assert_called_once_with()


def test_macOS_existing_install(test_command, tmp_path):
    """If there's an existing managed macOS JDK install, it is deleted and
    redownloaded."""
    # Force mocking on macOS
    test_command.host_os = "Darwin"

    # Create a mock of a previously installed Java version.
    java_home = tmp_path / "tools" / "java" / "Contents" / "Home"
    (java_home / "bin").mkdir(parents=True)

    # We actually need to delete the original java install
    def rmtree(path):
        shutil.rmtree(path)

    test_command.shutil.rmtree.side_effect = rmtree

    # Mock the cached download path.
    # Consider to remove if block when we drop py3.7 support, only keep statements from else.
    # MagicMock below py3.8 doesn't has __fspath__ attribute.
    if sys.version_info < (3, 8):
        archive = FsPathMock("/path/to/download.zip")
    else:
        archive = MagicMock()
        archive.__fspath__.return_value = "/path/to/download.zip"
    test_command.download_url.return_value = archive

    # Create a directory to make it look like Java was downloaded and unpacked.
    (tmp_path / "tools" / "jdk8u242-b08").mkdir(parents=True)

    # Create an SDK wrapper
    jdk = JDK(test_command, java_home=java_home)

    # Attempt an upgrade.
    jdk.upgrade()

    # The old version has been deleted
    test_command.shutil.rmtree.assert_called_with(tmp_path / "tools" / "java")

    # A download was initiated
    test_command.download_url.assert_called_with(
        url="https://github.com/AdoptOpenJDK/openjdk8-binaries/releases/download/"
        "jdk8u242-b08/OpenJDK8U-jdk_x64_mac_hotspot_8u242b08.tar.gz",
        download_path=tmp_path / "tools",
    )

    # The archive was unpacked.
    # TODO: Py3.6 compatibility; os.fsdecode not required in Py3.7
    test_command.shutil.unpack_archive.assert_called_with(
        "/path/to/download.zip", extract_dir=os.fsdecode(tmp_path / "tools")
    )
    # The original archive was deleted
    archive.unlink.assert_called_once_with()


def test_download_fail(test_command, tmp_path):
    """If there's an existing managed JDK install, it is deleted and
    redownloaded."""
    # Create a mock of a previously installed Java version.
    java_home = tmp_path / "tools" / "java"
    (java_home / "bin").mkdir(parents=True)

    # We actually need to delete the original java install
    def rmtree(path):
        shutil.rmtree(path)

    test_command.shutil.rmtree.side_effect = rmtree

    # Mock a failure on download
    test_command.download_url.side_effect = requests_exceptions.ConnectionError

    # Create an SDK wrapper
    jdk = JDK(test_command, java_home=java_home)

    # Attempt an upgrade. This will fail along with the download
    with pytest.raises(NetworkFailure):
        jdk.upgrade()

    # The old version has been deleted
    test_command.shutil.rmtree.assert_called_with(java_home)

    # A download was initiated
    test_command.download_url.assert_called_with(
        url="https://github.com/AdoptOpenJDK/openjdk8-binaries/releases/download/"
        "jdk8u242-b08/OpenJDK8U-jdk_x64_linux_hotspot_8u242b08.tar.gz",
        download_path=tmp_path / "tools",
    )

    # No attempt was made to unpack the archive
    assert test_command.shutil.unpack_archive.call_count == 0


def test_unpack_fail(test_command, tmp_path):
    """If there's an existing managed JDK install, it is deleted and
    redownloaded."""
    # Create a mock of a previously installed Java version.
    java_home = tmp_path / "tools" / "java"
    (java_home / "bin").mkdir(parents=True)

    # We actually need to delete the original java install
    def rmtree(path):
        shutil.rmtree(path)

    test_command.shutil.rmtree.side_effect = rmtree

    # Mock the cached download path
    # Consider to remove if block when we drop py3.7 support, only keep statements from else.
    # MagicMock below py3.8 doesn't has __fspath__ attribute.
    if sys.version_info < (3, 8):
        archive = FsPathMock("/path/to/download.zip")
    else:
        archive = MagicMock()
        archive.__fspath__.return_value = "/path/to/download.zip"
    test_command.download_url.return_value = archive

    # Mock an unpack failure due to an invalid archive
    test_command.shutil.unpack_archive.side_effect = shutil.ReadError

    # Create an SDK wrapper
    jdk = JDK(test_command, java_home=java_home)

    # Attempt an upgrade. This will fail.
    with pytest.raises(BriefcaseCommandError):
        jdk.upgrade()

    # The old version has been deleted
    test_command.shutil.rmtree.assert_called_with(java_home)

    # A download was initiated
    test_command.download_url.assert_called_with(
        url="https://github.com/AdoptOpenJDK/openjdk8-binaries/releases/download/"
        "jdk8u242-b08/OpenJDK8U-jdk_x64_linux_hotspot_8u242b08.tar.gz",
        download_path=tmp_path / "tools",
    )

    # The archive was unpacked.
    # TODO: Py3.6 compatibility; os.fsdecode not required in Py3.7
    test_command.shutil.unpack_archive.assert_called_with(
        "/path/to/download.zip", extract_dir=os.fsdecode(tmp_path / "tools")
    )
    # The original archive was not deleted
    assert archive.unlink.call_count == 0
