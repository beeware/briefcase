import os
import shutil
import subprocess
from pathlib import Path
from unittest import mock

import pytest

from briefcase.exceptions import (
    BriefcaseCommandError,
    IncompatibleToolError,
    MissingToolError,
    NetworkFailure,
    UnsupportedHostError,
)
from briefcase.integrations.java import JDK

from ...utils import assert_url_resolvable
from .conftest import JDK_BUILD, JDK_RELEASE

CALL_JAVA_HOME = mock.call(["/usr/libexec/java_home"])


def test_short_circuit(mock_tools):
    """Tool is not created if already cached."""
    mock_tools.java = "tool"

    tool = JDK.verify(mock_tools)

    assert tool == "tool"
    assert tool == mock_tools.java


def test_unsupported_os(mock_tools):
    """When host OS is not supported, an error is raised."""
    mock_tools.host_os = "wonky"

    with pytest.raises(
        UnsupportedHostError,
        match=f"{JDK.name} is not supported on wonky",
    ):
        JDK.verify(mock_tools)


def test_unsupported_arch(mock_tools):
    """When the architecture is not supported, an error is raised."""
    mock_tools.host_arch = "IA-64"

    with pytest.raises(
        IncompatibleToolError,
        match="Briefcase cannot install Java JDK on this machine.",
    ):
        JDK.verify(mock_tools)


def test_macos_tool_java_home(mock_tools, capsys):
    """On macOS, the /usr/libexec/java_home utility is checked."""
    # Mock being on macOS
    mock_tools.host_os = "Darwin"

    # Mock 2 calls to check_output.
    mock_tools.subprocess.check_output.side_effect = [
        "/path/to/java",
        f"javac {JDK_RELEASE}\n",
    ]

    # Create a JDK wrapper by verification
    JDK.verify(mock_tools)

    # The JDK should have the path returned by the tool
    assert mock_tools.java.java_home == Path("/path/to/java")

    assert mock_tools.subprocess.check_output.mock_calls == [
        CALL_JAVA_HOME,
        # Second is a call to verify a valid Java version
        mock.call([os.fsdecode(Path("/path/to/java/bin/javac")), "-version"]),
    ]

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
    (tmp_path / "tools/java17/Contents/Home/bin").mkdir(parents=True)

    # Create a JDK wrapper by verification
    jdk = JDK.verify(mock_tools)

    # The JDK should have the briefcase JAVA_HOME
    assert jdk.java_home == tmp_path / "tools/java17/Contents/Home"

    assert mock_tools.subprocess.check_output.mock_calls == [CALL_JAVA_HOME]

    # No console output
    output = capsys.readouterr()
    assert output.out == ""
    assert output.err == ""


def test_macos_wrong_jdk_version(mock_tools, tmp_path, capsys):
    """On macOS, if the libexec tool returns an unqualified JDK, the Briefcase JDK is
    used."""
    # Mock being on macOS
    mock_tools.host_os = "Darwin"

    # Mock 2 calls to check_output.
    mock_tools.subprocess.check_output.side_effect = [
        "/path/to/java",
        "java 1.8.0_352\n",
    ]

    # Create a directory to make it look like the Briefcase Java already exists.
    (tmp_path / "tools/java17/Contents/Home/bin").mkdir(parents=True)

    # Create a JDK wrapper by verification
    jdk = JDK.verify(mock_tools)

    # The JDK should have the briefcase JAVA_HOME
    assert jdk.java_home == tmp_path / "tools/java17/Contents/Home"

    assert mock_tools.subprocess.check_output.mock_calls == [
        CALL_JAVA_HOME,
        mock.call([os.fsdecode(Path("/path/to/java/bin/javac")), "-version"]),
    ]

    # No console output
    output = capsys.readouterr()
    assert output.out == ""
    assert output.err == ""


def test_macos_invalid_jdk_path(mock_tools, tmp_path, capsys):
    """On macOS, if the libexec tool points to non-JDK path, the Briefcase JDK is
    used."""
    # Mock being on macOS
    mock_tools.host_os = "Darwin"

    # Mock 2 calls to check_output.
    mock_tools.subprocess.check_output.side_effect = [
        "/path/to/java",
        IndexError,
    ]

    # Create a directory to make it look like the Briefcase Java already exists.
    (tmp_path / "tools/java17/Contents/Home/bin").mkdir(parents=True)

    # Create a JDK wrapper by verification
    jdk = JDK.verify(mock_tools)

    # The JDK should have the briefcase JAVA_HOME
    assert jdk.java_home == tmp_path / "tools/java17/Contents/Home"

    assert mock_tools.subprocess.check_output.mock_calls == [
        CALL_JAVA_HOME,
        mock.call([os.fsdecode(Path("/path/to/java/bin/javac")), "-version"]),
    ]

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
    mock_tools.subprocess.check_output.return_value = f"javac {JDK_RELEASE}\n"

    # Create a JDK wrapper by verification
    JDK.verify(mock_tools)

    # The JDK should have the path returned by the tool
    assert mock_tools.java.java_home == Path("/path/to/java")

    # A single call to check output
    mock_tools.subprocess.check_output.assert_called_once_with(
        [os.fsdecode(Path("/path/to/java/bin/javac")), "-version"],
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
    mock_tools.subprocess.check_output.return_value = f"javac {JDK_RELEASE}\n"

    # Create a JDK wrapper by verification
    JDK.verify(mock_tools)

    # The JDK should have the path returned by the tool
    assert mock_tools.java.java_home == Path("/path/to/java")

    # A single call to check output
    mock_tools.subprocess.check_output.assert_called_once_with(
        [os.fsdecode(Path("/path/to/java/bin/javac")), "-version"],
    ),

    # No console output
    output = capsys.readouterr()
    assert output.out == ""
    assert output.err == ""


@pytest.mark.parametrize(
    "host_os, java_home",
    [
        ("Linux", Path("tools", "java17")),
        ("Windows", Path("tools", "java17")),
        ("Darwin", Path("tools", "java17", "Contents", "Home")),
    ],
)
def test_invalid_jdk_version(mock_tools, host_os, java_home, tmp_path, capsys):
    """If the JDK pointed to by JAVA_HOME isn't a Java 8 JDK, the briefcase JDK is
    used."""
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
    )

    # Warning is shown for invalid JAVA_HOME
    output = capsys.readouterr()
    assert "WARNING: JAVA_HOME does not point to a Java 17 JDK" in output.out
    assert output.out.endswith("****\n")
    assert output.err == ""


@pytest.mark.parametrize(
    "host_os, java_home, error_type",
    [
        ("Linux", Path("tools", "java17"), FileNotFoundError),
        ("Linux", Path("tools", "java17"), NotADirectoryError),
        ("Windows", Path("tools", "java17"), FileNotFoundError),
        ("Windows", Path("tools", "java17"), NotADirectoryError),
        ("Darwin", Path("tools", "java17", "Contents", "Home"), FileNotFoundError),
        ("Darwin", Path("tools", "java17", "Contents", "Home"), NotADirectoryError),
    ],
)
def test_no_javac(mock_tools, host_os, java_home, error_type, tmp_path, capsys):
    """If the JAVA_HOME doesn't point to a location with a bin/javac, the briefcase JDK
    is used."""
    # Mock os
    mock_tools.host_os = host_os

    # Setup explicit JAVA_HOME
    mock_tools.os.environ = {"JAVA_HOME": "/path/to/nowhere"}

    # Mock return value from javac failing because executable doesn't exist
    # FileNotFoundError is raised if bin/javac doesn't exist.
    # NotADirectoryError is raised if the user-provided path in JAVA_HOME
    #   contains parts that exist in the filesystem but are not a directory.
    mock_tools.subprocess.check_output.side_effect = error_type

    # Create a directory to make it look like the Briefcase Java already exists.
    (tmp_path / java_home / "bin").mkdir(parents=True)

    # Create a JDK wrapper by verification
    JDK.verify(mock_tools)

    # The JAVA_HOME should point at the Briefcase-provided JDK
    assert mock_tools.java.java_home == tmp_path / java_home

    # A single call was made to check javac
    mock_tools.subprocess.check_output.assert_called_once_with(
        [os.fsdecode(Path("/path/to/nowhere/bin/javac")), "-version"],
    ),

    # Warning is shown for invalid JAVA_HOME
    output = capsys.readouterr()
    assert "WARNING: JAVA_HOME does not point to a JDK" in output.out
    assert output.out.endswith("****\n")
    assert output.err == ""


@pytest.mark.parametrize(
    "host_os, java_home",
    [
        ("Linux", Path("tools", "java17")),
        ("Windows", Path("tools", "java17")),
        ("Darwin", Path("tools", "java17", "Contents", "Home")),
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
    ),

    # Warning is shown for invalid JAVA_HOME
    output = capsys.readouterr()
    assert "WARNING: Unable to invoke the Java compiler" in output.out
    assert output.out.endswith("****\n")
    assert output.err == ""


@pytest.mark.parametrize(
    "host_os, java_home",
    [
        ("Linux", Path("tools", "java17")),
        ("Windows", Path("tools", "java17")),
        ("Darwin", Path("tools", "java17", "Contents", "Home")),
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
    ),

    # No console output (because Briefcase JDK exists)
    output = capsys.readouterr()
    assert (
        "WARNING: Unable to determine the version of Java that is installed"
        in output.out
    )
    assert output.out.endswith("****\n")
    assert output.err == ""


@pytest.mark.parametrize(
    "host_os, host_arch, jdk_url, jhome, is_32bit",
    [
        (
            "Darwin",
            "x86_64",
            "https://github.com/adoptium/temurin17-binaries/releases/download/"
            f"jdk-{JDK_RELEASE}+{JDK_BUILD}/OpenJDK17U-jdk_x64_mac_hotspot_{JDK_RELEASE}_{JDK_BUILD}.tar.gz",
            "java17/Contents/Home",
            False,
        ),
        (
            "Darwin",
            "arm64",
            "https://github.com/adoptium/temurin17-binaries/releases/download/"
            f"jdk-{JDK_RELEASE}+{JDK_BUILD}/OpenJDK17U-jdk_aarch64_mac_hotspot_{JDK_RELEASE}_{JDK_BUILD}.tar.gz",
            "java17/Contents/Home",
            False,
        ),
        (
            "Linux",
            "x86_64",
            "https://github.com/adoptium/temurin17-binaries/releases/download/"
            f"jdk-{JDK_RELEASE}+{JDK_BUILD}/OpenJDK17U-jdk_x64_linux_hotspot_{JDK_RELEASE}_{JDK_BUILD}.tar.gz",
            "java17",
            False,
        ),
        (
            "Linux",
            "aarch64",
            "https://github.com/adoptium/temurin17-binaries/releases/download/"
            f"jdk-{JDK_RELEASE}+{JDK_BUILD}/OpenJDK17U-jdk_aarch64_linux_hotspot_{JDK_RELEASE}_{JDK_BUILD}.tar.gz",
            "java17",
            False,
        ),
        (
            "Linux",
            "aarch64",
            "https://github.com/adoptium/temurin17-binaries/releases/download/"
            f"jdk-{JDK_RELEASE}+{JDK_BUILD}/OpenJDK17U-jdk_arm_linux_hotspot_{JDK_RELEASE}_{JDK_BUILD}.tar.gz",
            "java17",
            True,
        ),
        (
            "Linux",
            "armv7l",
            "https://github.com/adoptium/temurin17-binaries/releases/download/"
            f"jdk-{JDK_RELEASE}+{JDK_BUILD}/OpenJDK17U-jdk_arm_linux_hotspot_{JDK_RELEASE}_{JDK_BUILD}.tar.gz",
            "java17",
            False,
        ),
        (
            "Linux",
            "armv8l",
            "https://github.com/adoptium/temurin17-binaries/releases/download/"
            f"jdk-{JDK_RELEASE}+{JDK_BUILD}/OpenJDK17U-jdk_arm_linux_hotspot_{JDK_RELEASE}_{JDK_BUILD}.tar.gz",
            "java17",
            False,
        ),
        (
            "Windows",
            "AMD64",
            "https://github.com/adoptium/temurin17-binaries/releases/download/"
            f"jdk-{JDK_RELEASE}+{JDK_BUILD}/OpenJDK17U-jdk_x64_windows_hotspot_{JDK_RELEASE}_{JDK_BUILD}.zip",
            "java17",
            False,
        ),
    ],
)
def test_successful_jdk_download(
    mock_tools,
    tmp_path,
    capsys,
    host_os,
    host_arch,
    jdk_url,
    jhome,
    is_32bit,
):
    """If needed, a JDK can be downloaded."""
    # Mock host OS and arch
    mock_tools.host_os = host_os
    mock_tools.host_arch = host_arch
    mock_tools.is_32bit_python = is_32bit

    # Mock a JAVA_HOME that won't exist
    # This is only needed to make macOS *not* run /usr/libexec/java_home
    mock_tools.os.environ = {"JAVA_HOME": "/does/not/exist"}

    # Mock the cached download path
    archive = mock.MagicMock()
    archive.__fspath__.return_value = "/path/to/download.zip"
    mock_tools.download.file.return_value = archive

    # Create a directory to make it look like Java was downloaded and unpacked.
    (tmp_path / "tools" / f"jdk-{JDK_RELEASE}+{JDK_BUILD}").mkdir(parents=True)

    # Invoke the verify call
    JDK.verify(mock_tools)

    assert mock_tools.java.java_home == tmp_path / "tools" / jhome

    # Console output contains a warning about the bad JDK location
    output = capsys.readouterr()
    assert output.err == ""
    assert "** WARNING: JAVA_HOME does not point to a Java 17 JDK" in output.out

    # Download was invoked
    mock_tools.download.file.assert_called_with(
        url=jdk_url,
        download_path=tmp_path / "tools",
        role="Java 17 JDK",
    )
    # The archive was unpacked
    mock_tools.shutil.unpack_archive.assert_called_with(
        "/path/to/download.zip", extract_dir=os.fsdecode(tmp_path / "tools")
    )
    # The original archive was deleted
    archive.unlink.assert_called_once_with()
    # The download URL for JDK exists
    assert_url_resolvable(mock_tools.java.OpenJDK_download_url)


def test_not_installed(mock_tools, tmp_path):
    """If the JDK isn't installed, and install isn't requested, an error is raised."""
    # Mock host OS
    mock_tools.host_os = "Linux"

    # Invoke the verify call. Install is not requested, so this will fail.
    with pytest.raises(MissingToolError):
        JDK.verify(mock_tools, install=False)

    # Download was not invoked
    assert mock_tools.download.file.call_count == 0


def test_jdk_download_failure(mock_tools, tmp_path):
    """If an error occurs downloading the JDK, an error is raised."""
    # Mock Linux x86_64 as the host
    mock_tools.host_os = "Linux"
    mock_tools.host_arch = "x86_64"

    # Mock a failure on download
    mock_tools.download.file.side_effect = NetworkFailure("mock")

    # Invoking verify_jdk causes a network failure.
    with pytest.raises(NetworkFailure, match="Unable to mock"):
        JDK.verify(mock_tools)

    # That download was attempted
    mock_tools.download.file.assert_called_with(
        url="https://github.com/adoptium/temurin17-binaries/releases/download/"
        f"jdk-{JDK_RELEASE}+{JDK_BUILD}/OpenJDK17U-jdk_x64_linux_hotspot_{JDK_RELEASE}_{JDK_BUILD}.tar.gz",
        download_path=tmp_path / "tools",
        role="Java 17 JDK",
    )
    # No attempt was made to unpack the archive
    assert mock_tools.shutil.unpack_archive.call_count == 0


def test_invalid_jdk_archive(mock_tools, tmp_path):
    """If the JDK download isn't a valid archive, raise an error."""
    # Mock Linux x86_64 as the host
    mock_tools.host_os = "Linux"
    mock_tools.host_arch = "x86_64"

    # Mock the cached download path
    archive = mock.MagicMock()
    archive.__fspath__.return_value = "/path/to/download.zip"
    mock_tools.download.file.return_value = archive

    # Mock an unpack failure due to an invalid archive
    mock_tools.shutil.unpack_archive.side_effect = shutil.ReadError

    with pytest.raises(BriefcaseCommandError):
        JDK.verify(mock_tools)

    # The download occurred
    mock_tools.download.file.assert_called_with(
        url="https://github.com/adoptium/temurin17-binaries/releases/download/"
        f"jdk-{JDK_RELEASE}+{JDK_BUILD}/OpenJDK17U-jdk_x64_linux_hotspot_{JDK_RELEASE}_{JDK_BUILD}.tar.gz",
        download_path=tmp_path / "tools",
        role="Java 17 JDK",
    )
    # An attempt was made to unpack the archive.
    mock_tools.shutil.unpack_archive.assert_called_with(
        "/path/to/download.zip",
        extract_dir=os.fsdecode(tmp_path / "tools"),
    )
    # The original archive was not deleted
    assert archive.unlink.call_count == 0
