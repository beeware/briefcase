import os
import shutil
import subprocess
from pathlib import Path
from unittest import mock

import pytest

from briefcase.exceptions import BriefcaseCommandError, MissingToolError, NetworkFailure
from briefcase.integrations.java import JDK


def test_short_circuit(mock_tools):
    """Tool is not created if already cached."""
    mock_tools.java = "tool"

    tool = JDK.verify(mock_tools)

    assert tool == "tool"
    assert tool == mock_tools.java


def test_macos_tool_java_home(mock_tools, capsys):
    """On macOS, the /usr/libexec/java_home utility is checked."""
    # Mock being on macOS
    mock_tools.host_os = "Darwin"

    # Mock 2 calls to check_output.
    mock_tools.subprocess.check_output.side_effect = [
        "/path/to/java",
        "javac 1.8.0_144\n",
    ]

    # Create a JDK wrapper by verification
    JDK.verify(mock_tools)

    # The JDK should have the path returned by the tool
    assert mock_tools.java.java_home == Path("/path/to/java")

    mock_tools.subprocess.check_output.assert_has_calls(
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


def test_macos_tool_failure(mock_tools, tmp_path, capsys):
    """On macOS, if the libexec tool fails, the Briefcase JDK is used."""
    # Mock being on macOS
    mock_tools.host_os = "Darwin"

    # Mock a failed call on the libexec tool
    mock_tools.subprocess.check_output.side_effect = subprocess.CalledProcessError(
        returncode=1, cmd="/usr/libexec/java_home"
    )

    # Create a directory to make it look like the Briefcase Java already exists.
    (tmp_path / "tools" / "java" / "Contents" / "Home" / "bin").mkdir(parents=True)

    # Create a JDK wrapper by verification
    jdk = JDK.verify(mock_tools)

    # The JDK should have the briefcase JAVA_HOME
    assert jdk.java_home == tmp_path / "tools" / "java" / "Contents" / "Home"

    mock_tools.subprocess.check_output.assert_has_calls(
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


def test_macos_provided_overrides_tool_java_home(mock_tools, capsys):
    """On macOS, an explicit JAVA_HOME overrides /usr/libexec/java_home."""
    # Mock being on macOS
    mock_tools.host_os = "Darwin"

    # Setup explicit JAVA_HOME
    mock_tools.os.environ = {"JAVA_HOME": "/path/to/java"}

    # Mock return value from javac. libexec won't be invoked.
    mock_tools.subprocess.check_output.return_value = "javac 1.8.0_144\n"

    # Create a JDK wrapper by verification
    JDK.verify(mock_tools)

    # The JDK should have the path returned by the tool
    assert mock_tools.java.java_home == Path("/path/to/java")

    # A single call to check output
    mock_tools.subprocess.check_output.assert_called_once_with(
        [os.fsdecode(Path("/path/to/java/bin/javac")), "-version"],
        stderr=subprocess.STDOUT,
    ),

    # No console output
    output = capsys.readouterr()
    assert output.out == ""
    assert output.err == ""


def test_valid_provided_java_home(mock_tools, capsys):
    """If a valid JAVA_HOME is provided, it is used."""
    # Setup explicit JAVA_HOME
    mock_tools.os.environ = {"JAVA_HOME": "/path/to/java"}

    # Mock return value from javac.
    mock_tools.subprocess.check_output.return_value = "javac 1.8.0_144\n"

    # Create a JDK wrapper by verification
    JDK.verify(mock_tools)

    # The JDK should have the path returned by the tool
    assert mock_tools.java.java_home == Path("/path/to/java")

    # A single call to check output
    mock_tools.subprocess.check_output.assert_called_once_with(
        [os.fsdecode(Path("/path/to/java/bin/javac")), "-version"],
        stderr=subprocess.STDOUT,
    ),

    # No console output
    output = capsys.readouterr()
    assert output.out == ""
    assert output.err == ""


@pytest.mark.parametrize(
    "host_os, java_home",
    [
        ("Linux", Path("tools", "java")),
        ("Windows", Path("tools", "java")),
        ("Darwin", Path("tools", "java", "Contents", "Home")),
    ],
)
def test_invalid_jdk_version(mock_tools, host_os, java_home, tmp_path, capsys):
    """If the JDK pointed to by JAVA_HOME isn't a Java 8 JDK, the briefcase JDK
    is used."""
    # Mock os
    mock_tools.host_os = host_os

    # Setup explicit JAVA_HOME
    mock_tools.os.environ = {"JAVA_HOME": "/path/to/java"}

    # Mock return value from javac.
    mock_tools.subprocess.check_output.return_value = "javac 14\n"

    # Create a directory to make it look like the Briefcase Java already exists.
    (tmp_path / java_home / "bin").mkdir(parents=True)

    # Create a JDK wrapper by verification
    JDK.verify(mock_tools)

    # The JDK should have the briefcase JAVA_HOME
    assert mock_tools.java.java_home == tmp_path / java_home

    # A single call was made to check javac
    mock_tools.subprocess.check_output.assert_called_once_with(
        [os.fsdecode(Path("/path/to/java/bin/javac")), "-version"],
        stderr=subprocess.STDOUT,
    )

    # No console output (because Briefcase JDK exists)
    output = capsys.readouterr()
    assert output.out == ""
    assert output.err == ""


@pytest.mark.parametrize(
    "host_os, java_home",
    [
        ("Linux", Path("tools", "java")),
        ("Windows", Path("tools", "java")),
        ("Darwin", Path("tools", "java", "Contents", "Home")),
    ],
)
def test_no_javac(mock_tools, host_os, java_home, tmp_path, capsys):
    """If the JAVA_HOME doesn't point to a location with a bin/javac, the
    briefcase JDK is used."""
    # Mock os
    mock_tools.host_os = host_os

    # Setup explicit JAVA_HOME
    mock_tools.os.environ = {"JAVA_HOME": "/path/to/nowhere"}

    # Mock return value from javac failing because executable doesn't exist
    mock_tools.subprocess.check_output.side_effect = FileNotFoundError

    # Create a directory to make it look like the Briefcase Java already exists.
    (tmp_path / java_home / "bin").mkdir(parents=True)

    # Create a JDK wrapper by verification
    JDK.verify(mock_tools)

    # The JAVA_HOME should point at the Briefcase-provided JDK
    assert mock_tools.java.java_home == tmp_path / java_home

    # A single call was made to check javac
    mock_tools.subprocess.check_output.assert_called_once_with(
        [os.fsdecode(Path("/path/to/nowhere/bin/javac")), "-version"],
        stderr=subprocess.STDOUT,
    ),

    # No console output (because Briefcase JDK exists)
    output = capsys.readouterr()
    assert output.out == ""
    assert output.err == ""


@pytest.mark.parametrize(
    "host_os, java_home",
    [
        ("Linux", Path("tools", "java")),
        ("Windows", Path("tools", "java")),
        ("Darwin", Path("tools", "java", "Contents", "Home")),
    ],
)
def test_javac_error(mock_tools, host_os, java_home, tmp_path, capsys):
    """If javac can't be executed, the briefcase JDK is used."""
    # Mock os
    mock_tools.host_os = host_os

    # Setup explicit JAVA_HOME
    mock_tools.os.environ = {"JAVA_HOME": "/path/to/nowhere"}

    # Mock return value from javac failing because executable doesn't exist
    mock_tools.subprocess.check_output.side_effect = subprocess.CalledProcessError(
        returncode=1, cmd="/path/to/java/bin/javac"
    )

    # Create a directory to make it look like the Briefcase Java already exists.
    (tmp_path / java_home / "bin").mkdir(parents=True)

    # Create a JDK wrapper by verification
    JDK.verify(mock_tools)

    # The JDK should have the briefcase JAVA_HOME
    assert mock_tools.java.java_home == tmp_path / java_home

    # A single call was made to check javac
    mock_tools.subprocess.check_output.assert_called_once_with(
        [os.fsdecode(Path("/path/to/nowhere/bin/javac")), "-version"],
        stderr=subprocess.STDOUT,
    ),

    # No console output (because Briefcase JDK exists)
    output = capsys.readouterr()
    assert output.out == ""
    assert output.err == ""


@pytest.mark.parametrize(
    "host_os, java_home",
    [
        ("Linux", Path("tools", "java")),
        ("Windows", Path("tools", "java")),
        ("Darwin", Path("tools", "java", "Contents", "Home")),
    ],
)
def test_unparseable_javac_version(mock_tools, host_os, java_home, tmp_path, capsys):
    """If the javac version can't be parsed, the briefcase JDK is used."""
    # Mock os
    mock_tools.host_os = host_os

    # Setup explicit JAVA_HOME
    mock_tools.os.environ = {"JAVA_HOME": "/path/to/nowhere"}

    # Mock return value from javac.
    mock_tools.subprocess.check_output.return_value = "NONSENSE\n"

    # Create a directory to make it look like the Briefcase Java already exists.
    (tmp_path / java_home / "bin").mkdir(parents=True)

    # Create a JDK wrapper by verification
    jdk = JDK.verify(mock_tools)

    # The JDK should have the briefcase JAVA_HOME
    assert jdk.java_home == tmp_path / java_home

    # A single call was made to check javac
    mock_tools.subprocess.check_output.assert_called_once_with(
        [os.fsdecode(Path("/path/to/nowhere/bin/javac")), "-version"],
        stderr=subprocess.STDOUT,
    ),

    # No console output (because Briefcase JDK exists)
    output = capsys.readouterr()
    assert output.out == ""
    assert output.err == ""


@pytest.mark.parametrize(
    "host_os, jdk_url, jhome",
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
    mock_tools,
    tmp_path,
    capsys,
    host_os,
    jdk_url,
    jhome,
):
    """If needed, a JDK can be downloaded."""
    # Mock host OS
    mock_tools.host_os = host_os

    # Mock a JAVA_HOME that won't exist
    # This is only needed to make macOS *not* run /usr/libexec/java_home
    mock_tools.os.environ = {"JAVA_HOME": "/does/not/exist"}

    # Mock the cached download path
    # Consider to remove if block when we drop py3.7 support, only keep statements from else.
    # MagicMock below py3.8 doesn't have __fspath__ attribute.
    archive = mock.MagicMock()
    archive.__fspath__.return_value = "/path/to/download.zip"
    mock_tools.download.file.return_value = archive

    # Create a directory to make it look like Java was downloaded and unpacked.
    (tmp_path / "tools" / "jdk8u242-b08").mkdir(parents=True)

    # Invoke the verify call
    JDK.verify(mock_tools)

    assert mock_tools.java.java_home == tmp_path / "tools" / jhome

    # Console output contains a warning about the bad JDK location
    output = capsys.readouterr()
    assert output.err == ""
    assert "** WARNING: JAVA_HOME does not point to a Java 8 JDK" in output.out

    # Download was invoked
    mock_tools.download.file.assert_called_with(
        url=jdk_url,
        download_path=tmp_path / "tools",
        role="Java 8 JDK",
    )
    # The archive was unpacked
    # TODO: Py3.6 compatibility; os.fsdecode not required in Py3.7
    mock_tools.shutil.unpack_archive.assert_called_with(
        "/path/to/download.zip", extract_dir=os.fsdecode(tmp_path / "tools")
    )
    # The original archive was deleted
    archive.unlink.assert_called_once_with()


def test_not_installed(mock_tools, tmp_path):
    """If the JDK isn't installed, and install isn't requested, an error is
    raised."""
    # Mock host OS
    mock_tools.host_os = "Linux"

    # Invoke the verify call. Install is not requested, so this will fail.
    with pytest.raises(MissingToolError):
        JDK.verify(mock_tools, install=False)

    # Download was not invoked
    assert mock_tools.download.file.call_count == 0


def test_jdk_download_failure(mock_tools, tmp_path):
    """If an error occurs downloading the JDK, an error is raised."""
    # Mock Linux as the host
    mock_tools.host_os = "Linux"

    # Mock a failure on download
    mock_tools.download.file.side_effect = NetworkFailure("mock")

    # Invoking verify_jdk causes a network failure.
    with pytest.raises(NetworkFailure, match="Unable to mock"):
        JDK.verify(mock_tools)

    # That download was attempted
    mock_tools.download.file.assert_called_with(
        url="https://github.com/AdoptOpenJDK/openjdk8-binaries/releases/download/"
        "jdk8u242-b08/OpenJDK8U-jdk_x64_linux_hotspot_8u242b08.tar.gz",
        download_path=tmp_path / "tools",
        role="Java 8 JDK",
    )
    # No attempt was made to unpack the archive
    assert mock_tools.shutil.unpack_archive.call_count == 0


def test_invalid_jdk_archive(mock_tools, tmp_path):
    """If the JDK download isn't a valid archive, raise an error."""
    # Mock Linux as the host
    mock_tools.host_os = "Linux"

    # Mock the cached download path
    # Consider to remove if block when we drop py3.7 support, only keep statements from else.
    # MagicMock below py3.8 doesn't have __fspath__ attribute.
    archive = mock.MagicMock()
    archive.__fspath__.return_value = "/path/to/download.zip"
    mock_tools.download.file.return_value = archive

    # Mock an unpack failure due to an invalid archive
    mock_tools.shutil.unpack_archive.side_effect = shutil.ReadError

    with pytest.raises(BriefcaseCommandError):
        JDK.verify(mock_tools)

    # The download occurred
    mock_tools.download.file.assert_called_with(
        url="https://github.com/AdoptOpenJDK/openjdk8-binaries/releases/download/"
        "jdk8u242-b08/OpenJDK8U-jdk_x64_linux_hotspot_8u242b08.tar.gz",
        download_path=tmp_path / "tools",
        role="Java 8 JDK",
    )
    # An attempt was made to unpack the archive.
    # TODO: Py3.6 compatibility; os.fsdecode not required in Py3.7
    mock_tools.shutil.unpack_archive.assert_called_with(
        "/path/to/download.zip", extract_dir=os.fsdecode(tmp_path / "tools")
    )
    # The original archive was not deleted
    assert archive.unlink.call_count == 0
