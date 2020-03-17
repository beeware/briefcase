import subprocess
from io import BytesIO
from os import X_OK, access
from unittest import mock
from sys import platform
from zipfile import ZipFile

import pytest
from requests import exceptions as requests_exceptions

from briefcase.exceptions import BriefcaseCommandError, NetworkFailure
from briefcase.platforms.android.apk import ApkBuildCommand


def create_mock_android_sdk_zip(sdkmanager_name):
    """Create ZIP file data similar to the Android SDK."""
    out = BytesIO()
    with ZipFile(out, "w") as zipfile:
        zipfile.writestr("tools/bin/" + sdkmanager_name, "")
    return out.getvalue()


@pytest.fixture
def build_command(tmp_path, first_app_config):
    command = ApkBuildCommand(
        base_path=tmp_path / "base_path", apps={"first": first_app_config},
    )
    command.dot_briefcase_path = tmp_path / ".briefcase" / "tools"
    command.os = mock.MagicMock()
    command.os.environ = {}
    command.sys = mock.MagicMock()
    command.requests = mock.MagicMock()
    command.subprocess = mock.MagicMock()
    return command


def test_sdk_url(build_command):
    "Validate that the SDK URL is computed using `host_os`."
    # We set `host_os` to a sentinel value in order to validate that
    # `build_command.sdk_url` uses `host_os`.
    build_command.host_os = "sAMple"
    assert build_command.sdk_url == (
        "https://dl.google.com/android/repository/sdk-tools-sample-4333796.zip"
    )


def test_permit_python_37(build_command):
    "Validate that Python 3.7 is accepted." ""
    # Mock out the currently-running Python version to be 3.7.
    build_command.sys.version_info.major = 3
    build_command.sys.version_info.minor = 7
    build_command.verify_python_version()


@pytest.mark.parametrize("major,minor", [(3, 5), (3, 6), (3, 8)])
def test_require_python_37(build_command, major, minor):
    "Validate that Python versions other than 3.7 are rejected."
    # Mock out the Python version to check that version.
    build_command.sys.version_info.major = major
    build_command.sys.version_info.minor = minor
    with pytest.raises(BriefcaseCommandError):
        build_command.verify_python_version()


def test_verify_tools_succeeds_immediately_in_happy_path(build_command):
    """Validate that verify_tools() successfully does nothing in its happy
    path.

    If the Python version is 3.7. and `sdkmanager` exists and has the right
    permissions, and `android-sdk-license` exists, verify_tools() should
    succeed, create no subprocesses, and make no requests."""
    # Create `sdkmanager` and the license file.
    tools_bin = build_command.sdk_path / "tools" / "bin"
    tools_bin.mkdir(parents=True, mode=0o755)
    (tools_bin / "sdkmanager").touch(mode=0o755)
    licenses = build_command.sdk_path / "licenses"
    licenses.mkdir(parents=True, mode=0o755)
    (licenses / "android-sdk-license").touch()

    # Assume Python 3.7, to mollify verify_python_version().
    build_command.sys.version_info.major = 3
    build_command.sys.version_info.minor = 7

    # Expect verify_tools() to succeed and not call requests or subprocess.
    build_command.verify_tools()
    build_command.requests.get.assert_not_called()
    build_command.subprocess.run.assert_not_called()
    build_command.subprocess.check_output.assert_not_called()


def sdk_response(sdkmanager_name):
    response = mock.MagicMock()
    response.status_code = 200
    response.content = create_mock_android_sdk_zip(sdkmanager_name)
    response.headers = {}
    response.url = "http://example.com/sdk.zip"
    return response


@pytest.mark.parametrize("sdkmanager_name", ("sdkmanager", "sdkmanager.exe"))
def test_verify_sdk_downloads_sdk(build_command, sdkmanager_name, tmp_path):
    """Validate that verify_sdk() downloads & unpacks the SDK ZIP file,
    including setting permissions on `tools/bin/*` files."""
    sdkmanager = build_command.sdk_path / "tools" / "bin" / "sdkmanager"
    sdkmanagerexe = build_command.sdk_path / "tools" / "bin" / "sdkmanager.exe"
    # Assert that the file does not exist yet. We assert that it is created
    # below, which allows us to validate that the call to `verify_sdk()`
    # created it.
    assert not sdkmanager.exists() and not sdkmanagerexe.exists()
    build_command.requests.get.return_value = sdk_response(sdkmanager_name)
    build_command.verify_sdk()
    build_command.requests.get.assert_called_once_with(
        build_command.sdk_url, stream=True
    )
    assert sdkmanager.exists() or sdkmanagerexe.exists()
    assert access(str(sdkmanager), X_OK) or access(str(sdkmanagerexe), X_OK)


@pytest.mark.skipif(
    platform == "win32", reason="files are always executable on Windows"
)
@pytest.mark.parametrize("sdkmanager_name", ("sdkmanager", "sdkmanager.exe"))
def test_verify_sdk_downloads_sdk_if_sdkmanager_not_executable(
    build_command, sdkmanager_name
):
    """Validate that verify_sdk() downloads & unpacks the SDK ZIP file
    in the case that `tools/bin/sdkmanager` exists but does not have its
    permissions set properly."""
    build_command.requests.get.return_value = sdk_response(sdkmanager_name)
    (build_command.sdk_path / "tools" / "bin").mkdir(parents=True)
    (build_command.sdk_path / "tools" / "bin" / "sdkmanager").touch(mode=0o644)
    build_command.verify_sdk()
    build_command.requests.get.assert_called_once_with(
        build_command.sdk_url, stream=True
    )


@pytest.mark.parametrize("sdkmanager_name", ("sdkmanager", "sdkmanager.exe"))
def test_verify_sdk_no_download_if_sdkmanager_executable(
    build_command, sdkmanager_name
):
    """Validate that verify_sdk() successfully does nothing in its happy path.

    If `tools/bin/sdkmanager` exists with executable permissions, we expect
    verify_sdk() not to download the Android SDK."""
    build_command.requests.get.return_value = sdk_response(sdkmanager_name)
    (build_command.sdk_path / "tools" / "bin").mkdir(parents=True)
    (build_command.sdk_path / "tools" / "bin" / "sdkmanager").touch(mode=0o755)
    build_command.verify_sdk()
    build_command.requests.get.assert_not_called()


def test_verify_sdk_raises_networkfailure_on_connectionerror(build_command):
    """Validate that verify_sdk() raises the appropriate briefcase exception if
    an error occurs while downloading the ZIP file."""
    build_command.requests.get.side_effect = (
        requests_exceptions.ConnectionError()
    )
    with pytest.raises(NetworkFailure):
        build_command.verify_sdk()
    build_command.requests.get.assert_called_once_with(
        build_command.sdk_url, stream=True
    )


@pytest.fixture
def bad_zipfile_sdk_response():
    response = mock.MagicMock()
    response.status_code = 200
    response.content = b""
    response.headers = {}
    response.url = "http://example.com/sdk.zip"
    return response


def test_verify_sdk_detects_badzipfile(build_command, bad_zipfile_sdk_response):
    """Validate that verify_sdk() raises a briefcase exception if somehow a
    bad ZIP file was downloaded, or is found in its cache."""
    build_command.requests.get.return_value = bad_zipfile_sdk_response
    with pytest.raises(BriefcaseCommandError):
        build_command.verify_sdk()
    build_command.requests.get.assert_called_once_with(
        build_command.sdk_url, stream=True
    )


def test_verify_license_passes_quickly_if_license_present(build_command):
    """Validate that verify_license() successfully does nothing in its happy
    path.

    If `android-sdk-license` exists in the right place, we expect
    verify_license() to run no subprocesses."""
    license_path = build_command.sdk_path / "licenses" / "android-sdk-license"
    license_path.parent.mkdir(parents=True)
    license_path.touch()
    build_command.verify_license()
    build_command.subprocess.run.assert_not_called()


def test_verify_license_prompts_for_licenses_and_exits_if_you_agree(
    build_command,
):
    """Validate that if verify_license() succeeds if you agree to the Android
    SDK license."""

    def accept_license(*args, **kwargs):
        license_dir = build_command.sdk_path / "licenses"
        license_dir.mkdir(parents=True)
        (license_dir / "android-sdk-license").touch()

    build_command.subprocess.run.side_effect = accept_license
    build_command.verify_license()
    build_command.subprocess.run.assert_called_once_with(
        ["./sdkmanager", "--licenses"],
        check=True,
        cwd=str(build_command.sdk_path / "tools" / "bin"),
    )


def test_verify_license_handles_sdkmanager_crash(build_command,):
    """Validate that if verify_license() raises a briefcase exception if it
    fails to launch `sdkmanager`."""
    build_command.subprocess.run.side_effect = subprocess.CalledProcessError(
        1, ""
    )
    with pytest.raises(BriefcaseCommandError):
        build_command.verify_license()


def test_verify_license_insists_on_agreement(build_command):
    """Validate that if the user quits `sdkmanager --licenses` without agreeing
    to the license, verify_license() raises an exception."""
    # Simulate user non-acceptance of the license by allowing the mock
    # subprocess.run() to take no action.
    with pytest.raises(BriefcaseCommandError):
        build_command.verify_license()
