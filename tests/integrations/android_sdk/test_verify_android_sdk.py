import os
import shutil
import sys
from unittest.mock import MagicMock

import pytest
from requests import exceptions as requests_exceptions

from briefcase.exceptions import BriefcaseCommandError, NetworkFailure
from briefcase.integrations.android_sdk import verify_android_sdk


@pytest.fixture
def mock_command(tmp_path):
    command = MagicMock()

    # Mock-out the `sys` module so we can mock out the Python version in some tests.
    command.sys = MagicMock()

    # Use the `tmp_path` in `dot_briefcase_path` to ensure tests don't interfere
    # with each other.
    command.dot_briefcase_path = tmp_path / ".briefcase"

    # Make the `os` module and `host_os` live.
    command.os = os

    # Mock a host platform
    command.host_os = 'Unknown'

    # Override some other modules so we can test side-effects.
    command.download_url = MagicMock()
    command.subprocess = MagicMock()
    command.shutil = MagicMock()

    return command


def accept_license(android_sdk_root_path):
    "Generate a side effect method that will accept a license."
    def _side_effect(*args, **kwargs):
        license_dir = android_sdk_root_path / "licenses"
        license_dir.mkdir(parents=True)
        (license_dir / "android-sdk-license").touch()

    return _side_effect


@pytest.mark.parametrize("host_os", ("ArbitraryNotWindows", "Windows"))
def test_succeeds_immediately_in_happy_path(mock_command, host_os, tmp_path):
    "If verify_android_sdk is invoked on a path containing an Android SDK, it does nothing."
    # If `sdkmanager` exists and has the right permissions, and
    # `android-sdk-license` exists, verify_android_sdk() should
    # succeed, create no subprocesses, make no requests, and return a
    # SDK wrapper.

    # On Windows, this requires `sdkmanager.bat`; on non-Windows, it requires
    # `sdkmanager`.

    # Create `sdkmanager` and the license file.
    android_sdk_root_path = tmp_path / ".briefcase" / "tools" / "android_sdk"
    tools_bin = android_sdk_root_path / "tools" / "bin"
    tools_bin.mkdir(parents=True, mode=0o755)
    if host_os == "Windows":
        (tools_bin / "sdkmanager.bat").touch()
    else:
        (tools_bin / "sdkmanager").touch(mode=0o755)

    # Pre-accept the license
    accept_license(android_sdk_root_path)()

    # Configure `mock_command` to assume the `host_os` we parameterized with.
    mock_command.host_os = host_os

    # Expect verify_android_sdk() to succeed
    sdk = verify_android_sdk(mock_command)

    # No calls to download, run or unpack anything.
    mock_command.download_url.assert_not_called()
    mock_command.subprocess.run.assert_not_called()
    mock_command.subprocess.check_output.assert_not_called()
    mock_command.shutil.unpack_archive.assert_not_called()

    # The returned SDK has the expected root path.
    assert sdk.root_path == android_sdk_root_path


def test_user_provided_sdk(mock_command, tmp_path):
    "If the user specifies a valid ANDROID_SDK_ROOT, it is used"
    # Create `sdkmanager` and the license file.
    existing_android_sdk_root_path = tmp_path / "other_sdk"
    tools_bin = existing_android_sdk_root_path / "tools" / "bin"
    tools_bin.mkdir(parents=True, mode=0o755)
    (tools_bin / "sdkmanager").touch(mode=0o755)

    # Pre-accept the license
    accept_license(existing_android_sdk_root_path)()

    # Set the environment to specify ANDROID_SDK_ROOT
    mock_command.os.environ = {
        'ANDROID_SDK_ROOT': str(existing_android_sdk_root_path)
    }

    # Expect verify_android_sdk() to succeed
    sdk = verify_android_sdk(mock_command)

    # No calls to download, run or unpack anything.
    mock_command.download_url.assert_not_called()
    mock_command.subprocess.run.assert_not_called()
    mock_command.subprocess.check_output.assert_not_called()
    mock_command.shutil.unpack_archive.assert_not_called()

    # The returned SDK has the expected root path.
    # FIXME: The conversion to str is needed for Python 3.5 compatibility.
    assert str(sdk.root_path) == str(existing_android_sdk_root_path)


def test_invalid_user_provided_sdk(mock_command, tmp_path):
    "If the user specifies an invalid ANDROID_SDK_ROOT, it is ignored"

    # Create `sdkmanager` and the license file
    # for the *briefcase* SDK.
    android_sdk_root_path = tmp_path / ".briefcase" / "tools" / "android_sdk"
    tools_bin = android_sdk_root_path / "tools" / "bin"
    tools_bin.mkdir(parents=True, mode=0o755)
    (tools_bin / "sdkmanager").touch(mode=0o755)

    # Pre-accept the license
    accept_license(android_sdk_root_path)()

    # Set the environment to specify an ANDROID_SDK_ROOT that doesn't exist
    mock_command.os.environ = {
        'ANDROID_SDK_ROOT': str(tmp_path / "other_sdk")
    }

    # Expect verify_android_sdk() to succeed
    sdk = verify_android_sdk(mock_command)

    # No calls to download, run or unpack anything.
    mock_command.download_url.assert_not_called()
    mock_command.subprocess.run.assert_not_called()
    mock_command.subprocess.check_output.assert_not_called()
    mock_command.shutil.unpack_archive.assert_not_called()

    # The returned SDK has the expected root path.
    assert sdk.root_path == android_sdk_root_path


@pytest.mark.parametrize("host_os", ("ArbitraryNotWindows", "Windows"))
def test_download_sdk(mock_command, tmp_path, host_os):
    "If an SDK is not available, one will be downloaded"
    android_sdk_root_path = tmp_path / ".briefcase" / "tools" / "android_sdk"

    # Mock-out `host_os` so we only do our permission check on non-Windows.
    mock_command.host_os = host_os

    # The download will produce a cached file
    cache_file = MagicMock()
    cache_file.__str__.return_value = "/path/to/download.zip"
    mock_command.download_url.return_value = cache_file

    # Create a file that would have been created by unpacking the archive
    example_tool = android_sdk_root_path / "tools" / "bin" / "exampletool"
    example_tool.parent.mkdir(parents=True)
    example_tool.touch(0o644)

    # Set up a side effect for accepting the license
    mock_command.subprocess.run.side_effect = accept_license(android_sdk_root_path)

    # Call `verify_android_sdk()`
    sdk = verify_android_sdk(mock_command)

    # Validate that the SDK was downloaded and unpacked
    url = "https://dl.google.com/android/repository/sdk-tools-{host_os}-4333796.zip".format(
        host_os=host_os.lower()
    )
    mock_command.download_url.assert_called_once_with(
        url=url,
        download_path=mock_command.dot_briefcase_path / "tools",
    )
    mock_command.shutil.unpack_archive.assert_called_once_with(
        "/path/to/download.zip",
        extract_dir=str(android_sdk_root_path)
    )

    # The cached file will be deleeted
    cache_file.unlink.assert_called_once_with()

    # On non-Windows, ensure the unpacked binary was made executable
    if host_os != 'Windows':
        assert os.access(str(example_tool), os.X_OK)

    # The license has been accepted
    assert (android_sdk_root_path / "licenses" / "android-sdk-license").exists()

    # The returned SDK has the expected root path.
    assert sdk.root_path == android_sdk_root_path


@pytest.mark.skipif(
    sys.platform == "win32", reason="executable permission doesn't make sense on Windows"
)
def test_download_sdk_if_sdkmanager_not_executable(mock_command, tmp_path):
    """An SDK will be downloaded and unpackged if `tools/bin/sdkmanager` exists
    but does not have its permissions set properly."""
    android_sdk_root_path = tmp_path / ".briefcase" / "tools" / "android_sdk"

    # Create non-executable `sdkmanager`.
    android_sdk_root_path = tmp_path / ".briefcase" / "tools" / "android_sdk"
    (android_sdk_root_path / "tools" / "bin").mkdir(parents=True)
    (android_sdk_root_path / "tools" / "bin" / "sdkmanager").touch(mode=0o644)

    # The download will produce a cached file
    cache_file = MagicMock()
    cache_file.__str__.return_value = "/path/to/download.zip"
    mock_command.download_url.return_value = cache_file

    # Set up a side effect for accepting the license
    mock_command.subprocess.run.side_effect = accept_license(android_sdk_root_path)

    # Call `verify_android_sdk()`
    sdk = verify_android_sdk(mock_command)

    # Validate that the SDK was downloaded and unpacked
    mock_command.download_url.assert_called_once_with(
        url="https://dl.google.com/android/repository/sdk-tools-unknown-4333796.zip",
        download_path=mock_command.dot_briefcase_path / "tools",
    )
    mock_command.shutil.unpack_archive.assert_called_once_with(
        "/path/to/download.zip",
        extract_dir=str(android_sdk_root_path)
    )

    # The cached file will be deleted
    cache_file.unlink.assert_called_once_with()

    # The license has been accepted
    assert (android_sdk_root_path / "licenses" / "android-sdk-license").exists()

    # The returned SDK has the expected root path.
    assert sdk.root_path == android_sdk_root_path


def test_raises_networkfailure_on_connectionerror(mock_command):
    "If an error occurs downloading the ZIP file, and error is raised."
    mock_command.download_url.side_effect = requests_exceptions.ConnectionError()

    with pytest.raises(NetworkFailure):
        verify_android_sdk(mock_command)

    # The download was attempted
    mock_command.download_url.assert_called_once_with(
        url="https://dl.google.com/android/repository/sdk-tools-unknown-4333796.zip",
        download_path=mock_command.dot_briefcase_path / "tools",
    )
    # But no unpack occurred
    assert mock_command.shutil.unpack_archive.call_count == 0


def test_detects_bad_zipfile(mock_command, tmp_path):
    "If the ZIP file is corrupted, an error is raised."
    android_sdk_root_path = tmp_path / ".briefcase" / "tools" / "android_sdk"

    # The download will produce a cached file
    cache_file = MagicMock()
    cache_file.__str__.return_value = "/path/to/download.zip"
    mock_command.download_url.return_value = cache_file

    # But the unpack will fail.
    mock_command.shutil.unpack_archive.side_effect = shutil.ReadError

    with pytest.raises(BriefcaseCommandError):
        verify_android_sdk(mock_command)

    # The download attempt was made.
    mock_command.download_url.assert_called_once_with(
        url="https://dl.google.com/android/repository/sdk-tools-unknown-4333796.zip",
        download_path=mock_command.dot_briefcase_path / "tools",
    )
    mock_command.shutil.unpack_archive.assert_called_once_with(
        "/path/to/download.zip",
        extract_dir=str(android_sdk_root_path)
    )
