import os
import platform
import shutil
import sys
from unittest.mock import MagicMock

import pytest

from briefcase.exceptions import BriefcaseCommandError, MissingToolError, NetworkFailure
from briefcase.integrations.android_sdk import AndroidSDK
from briefcase.integrations.base import ToolCache


@pytest.fixture
def mock_tools(mock_tools) -> ToolCache:
    # Mock the os environment, but copy over other key functions.
    mock_tools.os.environ = {}
    mock_tools.os.fsdecode = os.fsdecode
    mock_tools.os.access = os.access

    # Identify the host platform
    mock_tools._test_download_tag = {
        "Windows": "win",
        "Darwin": "mac",
        "Linux": "linux",
    }[mock_tools.host_os]

    # Use the original module rmtree implementation
    mock_tools.shutil.rmtree = shutil.rmtree

    return mock_tools


def mock_unpack(filename, extract_dir):
    # Create a file that would have been created by unpacking the archive
    # This includes the duplicated "cmdline-tools" folder name
    (extract_dir / "cmdline-tools" / "bin").mkdir(parents=True)
    (extract_dir / "cmdline-tools" / "bin" / "sdkmanager").touch(mode=0o644)
    (extract_dir / "cmdline-tools" / "bin" / "avdmanager").touch(mode=0o644)
    # Include an extra tool that is already executable.
    (extract_dir / "cmdline-tools" / "bin" / "other").touch(mode=0o755)


def accept_license(android_sdk_root_path):
    """Generate a side effect method that will accept a license."""

    def _side_effect(*args, **kwargs):
        license_dir = android_sdk_root_path / "licenses"
        license_dir.mkdir(parents=True)
        (license_dir / "android-sdk-license").touch()

    return _side_effect


def test_short_circuit(mock_tools):
    """Tool is not created if already cached."""
    mock_tools.android_sdk = "tool"

    tool = AndroidSDK.verify(mock_tools)

    assert tool == "tool"
    assert tool == mock_tools.android_sdk


def test_succeeds_immediately_in_happy_path(mock_tools, tmp_path):
    """If verify is invoked on a path containing an Android SDK, it does
    nothing."""
    # If `sdkmanager` exists and has the right permissions, and
    # `android-sdk-license` exists, verify() should
    # succeed, create no subprocesses, make no requests, and return a
    # SDK wrapper.

    # On Windows, this requires `sdkmanager.bat`; on non-Windows, it requires
    # `sdkmanager`.

    # Create `sdkmanager` and the license file.
    android_sdk_root_path = tmp_path / "tools" / "android_sdk"
    tools_bin = android_sdk_root_path / "cmdline-tools" / "latest" / "bin"
    tools_bin.mkdir(parents=True, mode=0o755)
    if platform.system() == "Windows":
        sdk_manager = tools_bin / "sdkmanager.bat"
        sdk_manager.touch()
    else:
        sdk_manager = tools_bin / "sdkmanager"
        sdk_manager.touch(mode=0o755)

    # Pre-accept the license
    accept_license(android_sdk_root_path)()

    # Expect verify() to succeed
    sdk = AndroidSDK.verify(mock_tools)

    # No calls to download, run or unpack anything.
    mock_tools.download.file.assert_not_called()
    mock_tools.subprocess.run.assert_not_called()
    mock_tools.shutil.unpack_archive.assert_not_called()

    # The returned SDK has the expected root path.
    assert sdk.root_path == android_sdk_root_path


def test_succeeds_immediately_in_happy_path_with_debug(mock_tools, tmp_path):
    """If debug is enabled, a verify call will display the installed
    packages."""
    # Increase the log level.
    mock_tools.logger.verbosity = 2

    # If `sdkmanager` exists and has the right permissions, and
    # `android-sdk-license` exists, verify() should
    # succeed, create no subprocesses, make no requests, and return a
    # SDK wrapper.

    # On Windows, this requires `sdkmanager.bat`; on non-Windows, it requires
    # `sdkmanager`.

    # Create `sdkmanager` and the license file.
    android_sdk_root_path = tmp_path / "tools" / "android_sdk"
    tools_bin = android_sdk_root_path / "cmdline-tools" / "latest" / "bin"
    tools_bin.mkdir(parents=True, mode=0o755)
    if platform.system() == "Windows":
        sdk_manager = tools_bin / "sdkmanager.bat"
        sdk_manager.touch()
    else:
        sdk_manager = tools_bin / "sdkmanager"
        sdk_manager.touch(mode=0o755)

    # Pre-accept the license
    accept_license(android_sdk_root_path)()

    # Expect verify() to succeed
    sdk = AndroidSDK.verify(mock_tools)

    # No calls to download or unpack anything.
    mock_tools.download.file.assert_not_called()
    mock_tools.shutil.unpack_archive.assert_not_called()

    # The returned SDK has the expected root path.
    assert sdk.root_path == android_sdk_root_path


def test_user_provided_sdk(mock_tools, tmp_path):
    """If the user specifies a valid ANDROID_SDK_ROOT, it is used."""
    # Increase the log level.
    mock_tools.logger.verbosity = 2

    # Create `sdkmanager` and the license file.
    existing_android_sdk_root_path = tmp_path / "other_sdk"
    tools_bin = existing_android_sdk_root_path / "cmdline-tools" / "latest" / "bin"
    tools_bin.mkdir(parents=True, mode=0o755)
    if platform.system() == "Windows":
        sdk_manager = tools_bin / "sdkmanager.bat"
        sdk_manager.touch()
    else:
        sdk_manager = tools_bin / "sdkmanager"
        sdk_manager.touch(mode=0o755)

    # Pre-accept the license
    accept_license(existing_android_sdk_root_path)()

    # Set the environment to specify ANDROID_SDK_ROOT
    mock_tools.os.environ = {
        "ANDROID_SDK_ROOT": os.fsdecode(existing_android_sdk_root_path)
    }

    # Expect verify() to succeed
    sdk = AndroidSDK.verify(mock_tools)

    # No calls to download or unpack anything.
    mock_tools.download.file.assert_not_called()
    mock_tools.shutil.unpack_archive.assert_not_called()

    # The returned SDK has the expected root path.
    assert sdk.root_path == existing_android_sdk_root_path


def test_user_provided_sdk_with_debug(mock_tools, tmp_path):
    """If the has debug with a user-specified ANDROID_SDK_ROOT, the packages
    are listed."""
    # Create `sdkmanager` and the license file.
    existing_android_sdk_root_path = tmp_path / "other_sdk"
    tools_bin = existing_android_sdk_root_path / "cmdline-tools" / "latest" / "bin"
    tools_bin.mkdir(parents=True, mode=0o755)
    if platform.system() == "Windows":
        sdk_manager = tools_bin / "sdkmanager.bat"
        sdk_manager.touch()
    else:
        sdk_manager = tools_bin / "sdkmanager"
        sdk_manager.touch(mode=0o755)

    # Pre-accept the license
    accept_license(existing_android_sdk_root_path)()

    # Set the environment to specify ANDROID_SDK_ROOT
    mock_tools.os.environ = {
        "ANDROID_SDK_ROOT": os.fsdecode(existing_android_sdk_root_path)
    }

    # Expect verify() to succeed
    sdk = AndroidSDK.verify(mock_tools)

    # No calls to download, run or unpack anything.
    mock_tools.download.file.assert_not_called()
    mock_tools.subprocess.run.assert_not_called()
    mock_tools.shutil.unpack_archive.assert_not_called()

    # The returned SDK has the expected root path.
    assert sdk.root_path == existing_android_sdk_root_path


def test_invalid_user_provided_sdk(mock_tools, tmp_path):
    """If the user specifies an invalid ANDROID_SDK_ROOT, it is ignored."""

    # Create `sdkmanager` and the license file
    # for the *briefcase* managed version of the SDK.
    android_sdk_root_path = tmp_path / "tools" / "android_sdk"
    tools_bin = android_sdk_root_path / "cmdline-tools" / "latest" / "bin"
    tools_bin.mkdir(parents=True, mode=0o755)
    if platform.system() == "Windows":
        sdk_manager = tools_bin / "sdkmanager.bat"
        sdk_manager.touch()
    else:
        sdk_manager = tools_bin / "sdkmanager"
        sdk_manager.touch(mode=0o755)

    # Pre-accept the license
    accept_license(android_sdk_root_path)()

    # Set the environment to specify an ANDROID_SDK_ROOT that doesn't exist
    mock_tools.os.environ = {"ANDROID_SDK_ROOT": os.fsdecode(tmp_path / "other_sdk")}

    # Expect verify() to succeed
    sdk = AndroidSDK.verify(mock_tools)

    # No calls to download, run or unpack anything.
    mock_tools.download.file.assert_not_called()
    mock_tools.subprocess.run.assert_not_called()
    mock_tools.shutil.unpack_archive.assert_not_called()

    # The returned SDK has the expected root path.
    assert sdk.root_path == android_sdk_root_path


def test_download_sdk(mock_tools, tmp_path):
    """If an SDK is not available, one will be downloaded."""
    android_sdk_root_path = tmp_path / "tools" / "android_sdk"
    cmdline_tools_base_path = android_sdk_root_path / "cmdline-tools"

    # The download will produce a cached file.
    cache_file = MagicMock()
    mock_tools.download.file.return_value = cache_file

    # Calling unpack will create files
    mock_tools.shutil.unpack_archive.side_effect = mock_unpack

    # Set up a side effect for accepting the license
    mock_tools.subprocess.run.side_effect = accept_license(android_sdk_root_path)

    # Call `verify()`
    sdk = AndroidSDK.verify(mock_tools)

    # Validate that the SDK was downloaded and unpacked
    url = (
        "https://dl.google.com/android/repository/"
        f"commandlinetools-{mock_tools._test_download_tag}-8092744_latest.zip"
    )
    mock_tools.download.file.assert_called_once_with(
        url=url,
        download_path=mock_tools.base_path,
        role="Android SDK Command-Line Tools",
    )

    mock_tools.shutil.unpack_archive.assert_called_once_with(
        cache_file, extract_dir=cmdline_tools_base_path
    )

    # The cached file will be deleted
    cache_file.unlink.assert_called_once_with()

    # The commandline tools path exists, in both "latest" and versioned form
    assert sdk.cmdline_tools_path.exists()
    assert sdk.cmdline_tools_version_path.exists()

    # The versioned form is a marker file; the tools path is a live directory
    assert sdk.cmdline_tools_path.is_dir()
    assert sdk.cmdline_tools_version_path.is_file()

    if platform.system() != "Windows":
        # On non-Windows, ensure the unpacked binary was made executable
        assert os.access(
            cmdline_tools_base_path / "latest" / "bin" / "sdkmanager", os.X_OK
        )

    # The license has been accepted
    assert (android_sdk_root_path / "licenses" / "android-sdk-license").exists()

    # The returned SDK has the expected root path.
    assert sdk.root_path == android_sdk_root_path


def test_download_sdk_legacy_install(mock_tools, tmp_path):
    """If the legacy SDK tools are present, they will be deleted."""
    android_sdk_root_path = tmp_path / "tools" / "android_sdk"
    cmdline_tools_base_path = android_sdk_root_path / "cmdline-tools"

    # Create files that mock the existence of the *old* SDK tools.
    sdk_tools_base_path = android_sdk_root_path / "tools"
    (sdk_tools_base_path / "bin").mkdir(parents=True)
    (sdk_tools_base_path / "bin" / "sdkmanager").touch(mode=0o755)
    (sdk_tools_base_path / "bin" / "avdmanager").touch(mode=0o755)

    # Create some of the tools that have locations that overlap
    # between legacy and new.
    emulator_path = android_sdk_root_path / "emulator"
    emulator_path.mkdir(parents=True)
    (emulator_path / "emulator").touch(mode=0o755)

    # The download will produce a cached file.
    cache_file = MagicMock()
    mock_tools.download.file.return_value = cache_file

    # Calling unpack will create files
    mock_tools.shutil.unpack_archive.side_effect = mock_unpack

    # Set up a side effect for accepting the license
    mock_tools.subprocess.run.side_effect = accept_license(android_sdk_root_path)

    # Call `verify()`
    sdk = AndroidSDK.verify(mock_tools)

    # Validate that the SDK was downloaded and unpacked
    url = (
        "https://dl.google.com/android/repository/"
        f"commandlinetools-{mock_tools._test_download_tag}-8092744_latest.zip"
    )
    mock_tools.download.file.assert_called_once_with(
        url=url,
        download_path=mock_tools.base_path,
        role="Android SDK Command-Line Tools",
    )

    mock_tools.shutil.unpack_archive.assert_called_once_with(
        cache_file, extract_dir=cmdline_tools_base_path
    )

    # The cached file will be deleted
    cache_file.unlink.assert_called_once_with()

    # The commandline tools path exists, in both "latest" and versioned form
    assert sdk.cmdline_tools_path.exists()
    assert sdk.cmdline_tools_version_path.exists()

    # The versioned form is a marker file; the tools path is a live directory
    assert sdk.cmdline_tools_path.is_dir()
    assert sdk.cmdline_tools_version_path.is_file()

    if platform.system() != "Windows":
        # On non-Windows, ensure the unpacked binary was made executable
        assert os.access(
            cmdline_tools_base_path / "latest" / "bin" / "sdkmanager", os.X_OK
        )

    # The legacy SDK tools have been removed
    assert not sdk_tools_base_path.exists()
    assert not emulator_path.exists()

    # The license has been accepted
    assert (android_sdk_root_path / "licenses" / "android-sdk-license").exists()

    # The returned SDK has the expected root path.
    assert sdk.root_path == android_sdk_root_path


def test_no_install(mock_tools, tmp_path):
    """If an SDK is not available, and install is not requested, an error is
    raised."""

    # Call `verify()`
    with pytest.raises(MissingToolError):
        AndroidSDK.verify(mock_tools, install=False)

    assert mock_tools.download.file.call_count == 0


@pytest.mark.skipif(
    sys.platform == "win32",
    reason="executable permission doesn't make sense on Windows",
)
def test_download_sdk_if_sdkmanager_not_executable(mock_tools, tmp_path):
    """An SDK will be downloaded and unpacked if `tools/bin/sdkmanager` exists
    but does not have its permissions set properly."""
    android_sdk_root_path = tmp_path / "tools" / "android_sdk"
    cmdline_tools_base_path = android_sdk_root_path / "cmdline-tools"

    # Create pre-existing non-executable `sdkmanager`.
    (cmdline_tools_base_path / "latest" / "bin").mkdir(parents=True)
    (cmdline_tools_base_path / "latest" / "bin" / "sdkmanager").touch(mode=0o644)
    (cmdline_tools_base_path / "8092744").touch()

    # The download will produce a cached file
    cache_file = MagicMock()
    mock_tools.download.file.return_value = cache_file

    # Calling unpack will create files
    mock_tools.shutil.unpack_archive.side_effect = mock_unpack

    # Set up a side effect for accepting the license
    mock_tools.subprocess.run.side_effect = accept_license(android_sdk_root_path)

    # Call `verify()`
    sdk = AndroidSDK.verify(mock_tools)

    # Validate that the SDK was downloaded and unpacked
    url = (
        "https://dl.google.com/android/repository/"
        f"commandlinetools-{mock_tools._test_download_tag}-8092744_latest.zip"
    )
    mock_tools.download.file.assert_called_once_with(
        url=url,
        download_path=mock_tools.base_path,
        role="Android SDK Command-Line Tools",
    )

    mock_tools.shutil.unpack_archive.assert_called_once_with(
        cache_file,
        extract_dir=cmdline_tools_base_path,
    )

    # The cached file will be deleted
    cache_file.unlink.assert_called_once_with()

    # The license has been accepted
    assert (android_sdk_root_path / "licenses" / "android-sdk-license").exists()

    # The returned SDK has the expected root path.
    assert sdk.root_path == android_sdk_root_path


def test_raises_networkfailure_on_connectionerror(mock_tools):
    """If an error occurs downloading the ZIP file, and error is raised."""
    mock_tools.download.file.side_effect = NetworkFailure("mock")

    with pytest.raises(NetworkFailure, match="Unable to mock"):
        AndroidSDK.verify(mock_tools)

    # The download was attempted
    url = (
        "https://dl.google.com/android/repository/"
        f"commandlinetools-{mock_tools._test_download_tag}-8092744_latest.zip"
    )
    mock_tools.download.file.assert_called_once_with(
        url=url,
        download_path=mock_tools.base_path,
        role="Android SDK Command-Line Tools",
    )
    # But no unpack occurred
    assert mock_tools.shutil.unpack_archive.call_count == 0


def test_detects_bad_zipfile(mock_tools, tmp_path):
    """If the ZIP file is corrupted, an error is raised."""
    android_sdk_root_path = tmp_path / "tools" / "android_sdk"

    cache_file = MagicMock()
    mock_tools.download.file.return_value = cache_file

    # But the unpack will fail.
    mock_tools.shutil.unpack_archive.side_effect = shutil.ReadError

    with pytest.raises(BriefcaseCommandError):
        AndroidSDK.verify(mock_tools)

    # The download attempt was made.
    url = (
        "https://dl.google.com/android/repository/"
        f"commandlinetools-{mock_tools._test_download_tag}-8092744_latest.zip"
    )
    mock_tools.download.file.assert_called_once_with(
        url=url,
        download_path=mock_tools.base_path,
        role="Android SDK Command-Line Tools",
    )
    mock_tools.shutil.unpack_archive.assert_called_once_with(
        cache_file, extract_dir=android_sdk_root_path / "cmdline-tools"
    )
