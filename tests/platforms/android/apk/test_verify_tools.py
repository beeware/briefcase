import subprocess
from io import BytesIO
from stat import S_IMODE
from unittest import mock
from zipfile import ZipFile

import pytest
from requests import exceptions as requests_exceptions

from briefcase.exceptions import BriefcaseCommandError, NetworkFailure
from briefcase.platforms.android.apk import ApkBuildCommand


def create_sentinel_zipfile():
    out = BytesIO()
    with ZipFile(out, "w") as zipfile:
        zipfile.writestr("tools/bin/sdkmanager", "")
    return out.getvalue()


@pytest.fixture
def build_command(tmp_path, first_app_config):
    class TestableApkBuildCommand(ApkBuildCommand):
        dot_briefcase = tmp_path / ".briefcase" / "tools"

    command = TestableApkBuildCommand(
        base_path=tmp_path / "base_path", apps={"first": first_app_config},
    )
    command.tmp_path = tmp_path
    command.host_os = "Linux"
    command.os = mock.MagicMock()
    command.os.environ = {}
    command.sys = mock.MagicMock()
    command.sys.version_info.major = 3
    command.sys.version_info.minor = 7
    command.requests = mock.MagicMock()
    command.subprocess = mock.MagicMock()
    return command


def test_sdk_url(build_command):
    build_command.host_os = "Linux"
    assert build_command.sdk_url == (
        "https://dl.google.com/android/repository/sdk-tools-linux-4333796.zip"
    )


def test_permit_python_37(build_command):
    build_command.verify_python_version()


@pytest.mark.parametrize("major,minor", [(3, 5), (3, 6), (3, 8)])
def test_require_python_37(build_command, major, minor):
    build_command.sys.version_info.major = major
    build_command.sys.version_info.minor = minor
    with pytest.raises(BriefcaseCommandError):
        build_command.verify_python_version()


def test_verify_tools_succeeds_immediately_when_tools_exist(build_command):
    # Create `sdkmanager` and the license file.
    tools_bin = build_command.sdk_path / "tools" / "bin"
    tools_bin.mkdir(parents=True, mode=0o755)
    (tools_bin / "sdkmanager").touch(mode=0o755)
    licenses = build_command.sdk_path / "licenses"
    licenses.mkdir(parents=True, mode=0o755)
    (licenses / "android-sdk-license").touch()

    # Expect verify_tools() to succeed and not call requests or subprocess.
    build_command.verify_tools()
    build_command.requests.get.assert_not_called()
    build_command.subprocess.run.assert_not_called()
    build_command.subprocess.check_output.assert_not_called()


@pytest.fixture
def sdk_response():
    response = mock.MagicMock()
    response.status_code = 200
    response.content = create_sentinel_zipfile()
    response.headers = {}
    response.url = "http://example.com/sdk.zip"
    return response


def test_verify_sdk_downloads_sdk(build_command, sdk_response, tmp_path):
    sdkmanager = build_command.sdk_path / "tools" / "bin" / "sdkmanager"
    # Assert that the file does not exist yet. We assert that it is created
    # below, which allows us to validate that the call to `verify_sdk()`
    # created it.
    assert not sdkmanager.exists()
    build_command.requests.get.return_value = sdk_response
    build_command.verify_sdk()
    build_command.requests.get.assert_called_once_with(
        build_command.sdk_url, stream=True
    )
    assert sdkmanager.exists()
    assert S_IMODE(sdkmanager.stat().st_mode) == 0o755


def test_verify_sdk_downloads_sdk_if_sdkmanager_not_executable(
    build_command, sdk_response
):
    build_command.requests.get.return_value = sdk_response
    (build_command.sdk_path / "tools" / "bin").mkdir(parents=True)
    (build_command.sdk_path / "tools" / "bin" / "sdkmanager").touch(mode=0o644)
    build_command.verify_sdk()
    build_command.requests.get.assert_called_once_with(
        build_command.sdk_url, stream=True
    )


def test_verify_sdk_no_download_if_sdkmanager_executable(build_command, sdk_response):
    build_command.requests.get.return_value = sdk_response
    (build_command.sdk_path / "tools" / "bin").mkdir(parents=True)
    (build_command.sdk_path / "tools" / "bin" / "sdkmanager").touch(mode=0o755)
    build_command.verify_sdk()
    build_command.requests.get.assert_not_called()


def test_verify_sdk_raises_networkfailure_on_connectionerror(build_command):
    build_command.requests.get.side_effect = requests_exceptions.ConnectionError()
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
    build_command.requests.get.return_value = bad_zipfile_sdk_response
    with pytest.raises(BriefcaseCommandError):
        build_command.verify_sdk()
    build_command.requests.get.assert_called_once_with(
        build_command.sdk_url, stream=True
    )


def test_verify_license_passes_quickly_if_license_present(build_command):
    license_path = build_command.sdk_path / "licenses" / "android-sdk-license"
    license_path.parent.mkdir(parents=True)
    license_path.touch()
    build_command.verify_license()
    build_command.subprocess.run.assert_not_called()


def test_verify_license_prompts_for_licenses_and_exits_if_you_agree(build_command,):
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
    build_command.subprocess.run.side_effect = subprocess.CalledProcessError(1, "")
    with pytest.raises(BriefcaseCommandError):
        build_command.verify_license()


def test_verify_license_insists_on_agreement(build_command):
    # If the user quits `sdkmanager --licenses` without agreeing to the license,
    # expect an error message from verify_license(). We simulate that by
    # allowing the mock subprocess.run() to take no action.
    with pytest.raises(BriefcaseCommandError):
        build_command.verify_license()
