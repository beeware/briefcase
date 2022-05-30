import os
import shutil
import subprocess
import sys
from pathlib import Path
from unittest import mock

import pytest
from requests import exceptions as requests_exceptions

from briefcase.console import Log
from briefcase.exceptions import BriefcaseCommandError, MissingToolError, NetworkFailure
from briefcase.integrations.java import JDK
from tests.utils import FsPathMock


@pytest.fixture
def test_command(tmp_path):
    command = mock.MagicMock()
    command.logger = Log()
    command.tools_path = tmp_path / "tools"

    # Mock environ.get returning no explicit JAVA_HOME
    command.os.environ.get = mock.MagicMock(return_value="")

    return command


def test_macos_tool_java_home(test_command, capsys):
    """On macOS, the /usr/libexec/java_home utility is checked."""
    # Mock being on macOS
    test_command.host_os = "Darwin"

    # Mock 2 calls to check_output.
    test_command.subprocess.check_output.side_effect = [
        "/path/to/java",
        "javac 1.8.0_144\n",
    ]

    # Create a JDK wrapper by verification
    jdk = JDK.verify(command=test_command)

    # The JDK should have the path returned by the tool
    assert jdk.java_home == Path("/path/to/java")

    test_command.subprocess.check_output.assert_has_calls(
        [
            # First call is to /usr/lib/java_home
            mock.call(
                ["/usr/libexec/java_home"],
                stderr=subprocess.STDOUT,
            ),
            # Second is a call to verify a valid Java version
            mock.call(
                [os.fsdecode(Path("/path/to/java/bin/javac")), "-version"],
                stderr=subprocess.STDOUT,
            ),
        ]
    )

    # No console output
    output = capsys.readouterr()
    assert output.out == ""
    assert output.err == ""


def test_macos_tool_failure(test_command, tmp_path, capsys):
    """On macOS, if the libexec tool fails, the Briefcase JDK is used."""
    # Mock being on macOS
    test_command.host_os = "Darwin"

    # Mock a failed call on the libexec tool
    test_command.subprocess.check_output.side_effect = subprocess.CalledProcessError(
        returncode=1, cmd="/usr/libexec/java_home"
    )

    # Create a directory to make it look like the Briefcase Java already exists.
    (tmp_path / "tools" / "java" / "Contents" / "Home" / "bin").mkdir(parents=True)

    # Create a JDK wrapper by verification
    jdk = JDK.verify(command=test_command)

    # The JDK should have the briefcase JAVA_HOME
    assert jdk.java_home == tmp_path / "tools" / "java" / "Contents" / "Home"

    test_command.subprocess.check_output.assert_has_calls(
        [
            # First call is to /usr/lib/java_home
            mock.call(
                ["/usr/libexec/java_home"],
                stderr=subprocess.STDOUT,
            ),
        ]
    )

    # No console output
    output = capsys.readouterr()
    assert output.out == ""
    assert output.err == ""


def test_macos_provided_overrides_tool_java_home(test_command, capsys):
    """On macOS, an explicit JAVA_HOME overrides /usr/libexec/java_home."""
    # Mock being on macOS
    test_command.host_os = "Darwin"

    # Mock environ.get returning an explicit JAVA_HOME
    test_command.os.environ.get = mock.MagicMock(return_value="/path/to/java")

    # Mock return value from javac. libexec won't be invoked.
    test_command.subprocess.check_output.return_value = "javac 1.8.0_144\n"

    # Create a JDK wrapper by verification
    jdk = JDK.verify(command=test_command)

    # The JDK should have the path returned by the tool
    assert jdk.java_home == Path("/path/to/java")

    # A single call to check output
    test_command.subprocess.check_output.assert_called_once_with(
        [os.fsdecode(Path("/path/to/java/bin/javac")), "-version"],
        stderr=subprocess.STDOUT,
    ),

    # No console output
    output = capsys.readouterr()
    assert output.out == ""
    assert output.err == ""


def test_valid_provided_java_home(test_command, capsys):
    """If a valid JAVA_HOME is provided, it is used."""
    # Mock environ.get returning an explicit JAVA_HOME
    test_command.os.environ.get = mock.MagicMock(return_value="/path/to/java")

    # Mock return value from javac.
    test_command.subprocess.check_output.return_value = "javac 1.8.0_144\n"

    # Create a JDK wrapper by verification
    jdk = JDK.verify(command=test_command)

    # The JDK should have the path returned by the tool
    assert jdk.java_home == Path("/path/to/java")

    # A single call to check output
    test_command.subprocess.check_output.assert_called_once_with(
        [os.fsdecode(Path("/path/to/java/bin/javac")), "-version"],
        stderr=subprocess.STDOUT,
    ),

    # No console output
    output = capsys.readouterr()
    assert output.out == ""
    assert output.err == ""


def test_invalid_jdk_version(test_command, tmp_path, capsys):
    """If the JDK pointed to by JAVA_HOME isn't a Java 8 JDK, the briefcase JDK
    is used."""
    # Mock environ.get returning an explicit JAVA_HOME
    test_command.os.environ.get = mock.MagicMock(return_value="/path/to/java")

    # Mock return value from javac.
    test_command.subprocess.check_output.return_value = "javac 14\n"

    # Create a directory to make it look like the Briefcase Java already exists.
    (tmp_path / "tools" / "java" / "bin").mkdir(parents=True)

    # Create a JDK wrapper by verification
    jdk = JDK.verify(command=test_command)

    # The JDK should have the briefcase JAVA_HOME
    assert jdk.java_home == tmp_path / "tools" / "java"

    # A single call was made to check javac
    test_command.subprocess.check_output.assert_called_once_with(
        [os.fsdecode(Path("/path/to/java/bin/javac")), "-version"],
        stderr=subprocess.STDOUT,
    ),

    # No console output (because Briefcase JDK exists)
    output = capsys.readouterr()
    assert output.out == ""
    assert output.err == ""


def test_no_javac(test_command, tmp_path, capsys):
    """If the JAVA_HOME doesn't point to a location with a bin/javac, the
    briefcase JDK is used."""
    # Mock environ.get returning an explicit JAVA_HOME
    test_command.os.environ.get = mock.MagicMock(return_value="/path/to/nowhere")

    # Mock return value from javac failing because executable doesn't exist
    test_command.subprocess.check_output.side_effect = FileNotFoundError

    # Create a directory to make it look like the Briefcase Java already exists.
    (tmp_path / "tools" / "java" / "bin").mkdir(parents=True)

    # Create a JDK wrapper by verification
    jdk = JDK.verify(command=test_command)

    # The JAVA_HOME should point at the Briefcase-provided JDK
    assert jdk.java_home == tmp_path / "tools" / "java"

    # A single call was made to check javac
    test_command.subprocess.check_output.assert_called_once_with(
        [os.fsdecode(Path("/path/to/nowhere/bin/javac")), "-version"],
        stderr=subprocess.STDOUT,
    ),

    # No console output (because Briefcase JDK exists)
    output = capsys.readouterr()
    assert output.out == ""
    assert output.err == ""


def test_javac_error(test_command, tmp_path, capsys):
    """If javac can't be executed, the briefcase JDK is used."""
    # Mock environ.get returning an explicit JAVA_HOME
    test_command.os.environ.get = mock.MagicMock(return_value="/path/to/java")

    # Mock return value from javac failing because executable doesn't exist
    test_command.subprocess.check_output.side_effect = subprocess.CalledProcessError(
        returncode=1, cmd="/path/to/java/bin/javac"
    )

    # Create a directory to make it look like the Briefcase Java already exists.
    (tmp_path / "tools" / "java" / "bin").mkdir(parents=True)

    # Create a JDK wrapper by verification
    jdk = JDK.verify(command=test_command)

    # The JDK should have the briefcase JAVA_HOME
    assert jdk.java_home == tmp_path / "tools" / "java"

    # A single call was made to check javac
    test_command.subprocess.check_output.assert_called_once_with(
        [os.fsdecode(Path("/path/to/java/bin/javac")), "-version"],
        stderr=subprocess.STDOUT,
    ),

    # No console output (because Briefcase JDK exists)
    output = capsys.readouterr()
    assert output.out == ""
    assert output.err == ""


def test_unparseable_javac_version(test_command, tmp_path, capsys):
    """If the javac version can't be parsed, the briefcase JDK is used."""
    # Mock environ.get returning an explicit JAVA_HOME
    test_command.os.environ.get = mock.MagicMock(return_value="/path/to/java")

    # Mock return value from javac.
    test_command.subprocess.check_output.return_value = "NONSENSE\n"

    # Create a directory to make it look like the Briefcase Java already exists.
    (tmp_path / "tools" / "java" / "bin").mkdir(parents=True)

    # Create a JDK wrapper by verification
    jdk = JDK.verify(command=test_command)

    # The JDK should have the briefcase JAVA_HOME
    assert jdk.java_home == tmp_path / "tools" / "java"

    # A single call was made to check javac
    test_command.subprocess.check_output.assert_called_once_with(
        [os.fsdecode(Path("/path/to/java/bin/javac")), "-version"],
        stderr=subprocess.STDOUT,
    ),

    # No console output (because Briefcase JDK exists)
    output = capsys.readouterr()
    assert output.out == ""
    assert output.err == ""


@pytest.mark.parametrize(
    ("host_os, jdk_url, jhome"),
    [
        (
            "Darwin",
            "https://github.com/AdoptOpenJDK/openjdk8-binaries/releases/download/"
            "jdk8u242-b08/OpenJDK8U-jdk_x64_mac_hotspot_8u242b08.tar.gz",
            "java/Contents/Home",
        ),
        (
            "Linux",
            "https://github.com/AdoptOpenJDK/openjdk8-binaries/releases/download/"
            "jdk8u242-b08/OpenJDK8U-jdk_x64_linux_hotspot_8u242b08.tar.gz",
            "java",
        ),
        (
            "Windows",
            "https://github.com/AdoptOpenJDK/openjdk8-binaries/releases/download/"
            "jdk8u242-b08/OpenJDK8U-jdk_x64_windows_hotspot_8u242b08.zip",
            "java",
        ),
    ],
)
def test_successful_jdk_download(
    test_command, tmp_path, capsys, host_os, jdk_url, jhome
):
    """If needed, a JDK can be downloaded."""
    # Mock host OS
    test_command.host_os = host_os

    # Mock a JAVA_HOME that won't exist
    # This is only needed to make macOS *not* run /usr/libexec/java_home
    test_command.os.environ.get = mock.MagicMock(return_value="/does/not/exist")

    # Mock the cached download path
    # Consider to remove if block when we drop py3.7 support, only keep statements from else.
    # MagicMock below py3.8 doesn't has __fspath__ attribute.
    if sys.version_info < (3, 8):
        archive = FsPathMock("/path/to/download.zip")
    else:
        archive = mock.MagicMock()
        archive.__fspath__.return_value = "/path/to/download.zip"
    test_command.download_url.return_value = archive

    # Create a directory to make it look like Java was downloaded and unpacked.
    (tmp_path / "tools" / "jdk8u242-b08").mkdir(parents=True)

    # Invoke the verify call
    jdk = JDK.verify(command=test_command)

    assert jdk.java_home == tmp_path / "tools" / jhome

    # Console output contains a warning about the bad JDK location
    output = capsys.readouterr()
    assert output.err == ""
    assert "** WARNING: JAVA_HOME does not point to a Java 8 JDK" in output.out

    # Download was invoked
    test_command.download_url.assert_called_with(
        url=jdk_url,
        download_path=tmp_path / "tools",
    )
    # The archive was unpacked
    # TODO: Py3.6 compatibility; os.fsdecode not required in Py3.7
    test_command.shutil.unpack_archive.assert_called_with(
        "/path/to/download.zip", extract_dir=os.fsdecode(tmp_path / "tools")
    )
    # The original archive was deleted
    archive.unlink.assert_called_once_with()


def test_not_installed(test_command, tmp_path):
    """If the JDK isn't installed, and install isn't requested, an error is
    raised."""
    # Mock host OS
    test_command.host_os = "Linux"

    # Invoke the verify call. Install is not requested, so this will fail.
    with pytest.raises(MissingToolError):
        JDK.verify(command=test_command, install=False)

    # Download was not invoked
    assert test_command.download_url.call_count == 0


def test_jdk_download_failure(test_command, tmp_path):
    """If an error occurs downloading the JDK, an error is raised."""
    # Mock Linux as the host
    test_command.host_os = "Linux"

    # Mock a failure on download
    test_command.download_url.side_effect = requests_exceptions.ConnectionError

    # Invoking verify_jdk causes a network failure.
    with pytest.raises(NetworkFailure):
        JDK.verify(command=test_command)

    # That download was attempted
    test_command.download_url.assert_called_with(
        url="https://github.com/AdoptOpenJDK/openjdk8-binaries/releases/download/"
        "jdk8u242-b08/OpenJDK8U-jdk_x64_linux_hotspot_8u242b08.tar.gz",
        download_path=tmp_path / "tools",
    )
    # No attempt was made to unpack the archive
    assert test_command.shutil.unpack_archive.call_count == 0


def test_invalid_jdk_archive(test_command, tmp_path):
    """If the JDK download isn't a valid archive, raise an error."""
    # Mock Linux as the host
    test_command.host_os = "Linux"

    # Mock the cached download path
    # Consider to remove if block when we drop py3.7 support, only keep statements from else.
    # MagicMock below py3.8 doesn't has __fspath__ attribute.
    if sys.version_info < (3, 8):
        archive = FsPathMock("/path/to/download.zip")
    else:
        archive = mock.MagicMock()
        archive.__fspath__.return_value = "/path/to/download.zip"
    test_command.download_url.return_value = archive

    # Mock an unpack failure due to an invalid archive
    test_command.shutil.unpack_archive.side_effect = shutil.ReadError

    with pytest.raises(BriefcaseCommandError):
        JDK.verify(command=test_command)

    # The download occurred
    test_command.download_url.assert_called_with(
        url="https://github.com/AdoptOpenJDK/openjdk8-binaries/releases/download/"
        "jdk8u242-b08/OpenJDK8U-jdk_x64_linux_hotspot_8u242b08.tar.gz",
        download_path=tmp_path / "tools",
    )
    # An attempt was made to unpack the archive.
    # TODO: Py3.6 compatibility; os.fsdecode not required in Py3.7
    test_command.shutil.unpack_archive.assert_called_with(
        "/path/to/download.zip", extract_dir=os.fsdecode(tmp_path / "tools")
    )
    # The original archive was not deleted
    assert archive.unlink.call_count == 0
