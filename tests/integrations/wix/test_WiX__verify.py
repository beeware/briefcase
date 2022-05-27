import os
import sys
from unittest.mock import MagicMock

import pytest
from requests import exceptions as requests_exceptions

from briefcase.exceptions import BriefcaseCommandError, MissingToolError, NetworkFailure
from briefcase.integrations.wix import WIX_DOWNLOAD_URL, WiX
from tests.utils import FsPathMock


@pytest.fixture
def mock_command(tmp_path):
    command = MagicMock()
    command.host_os = "Windows"
    command.tools_path = tmp_path / "tools"

    return command


def test_non_windows_host(mock_command):
    """If the host OS isn't Windows, the validator fails."""

    # Set the host OS to something not Windows
    mock_command.host_os = "Other OS"

    with pytest.raises(BriefcaseCommandError, match="can only be created on Windows"):
        WiX.verify(mock_command)


def test_valid_wix_envvar(mock_command, tmp_path):
    """If the WiX envvar points to a valid WiX install, the validator
    succeeds."""
    # Mock the environment for a WiX install
    wix_path = tmp_path / "wix"
    mock_command.os.environ.get.return_value = os.fsdecode(wix_path)

    # Mock the interesting parts of a WiX install
    (wix_path / "bin").mkdir(parents=True)
    (wix_path / "bin" / "heat.exe").touch()
    (wix_path / "bin" / "light.exe").touch()
    (wix_path / "bin" / "candle.exe").touch()

    # Verify the install
    wix = WiX.verify(mock_command)

    # The environment was queried.
    mock_command.os.environ.get.assert_called_with("WIX")

    # The returned paths are as expected (and are the full paths)
    assert wix.heat_exe == tmp_path / "wix" / "bin" / "heat.exe"
    assert wix.light_exe == tmp_path / "wix" / "bin" / "light.exe"
    assert wix.candle_exe == tmp_path / "wix" / "bin" / "candle.exe"


def test_invalid_wix_envvar(mock_command, tmp_path):
    """If the WiX envvar points to an invalid WiX install, the validator
    fails."""
    # Mock the environment for a WiX install
    wix_path = tmp_path / "wix"
    mock_command.os.environ.get.return_value = os.fsdecode(wix_path)

    # Don't create the actual install, and then attempt to validate
    with pytest.raises(BriefcaseCommandError, match="does not point to an install"):
        WiX.verify(mock_command)


def test_existing_wix_install(mock_command, tmp_path):
    """If there's an existing managed WiX install, the validator succeeds."""
    # Mock the environment as if there is not WiX variable
    mock_command.os.environ.get.return_value = None

    # Create a mock of a previously installed WiX version.
    wix_path = tmp_path / "tools" / "wix"
    wix_path.mkdir(parents=True)
    (wix_path / "heat.exe").touch()
    (wix_path / "light.exe").touch()
    (wix_path / "candle.exe").touch()

    wix = WiX.verify(mock_command)

    # The environment was queried.
    mock_command.os.environ.get.assert_called_with("WIX")

    # No download was attempted
    assert mock_command.download_url.call_count == 0

    # The returned paths are as expected
    assert wix.heat_exe == tmp_path / "tools" / "wix" / "heat.exe"
    assert wix.light_exe == tmp_path / "tools" / "wix" / "light.exe"
    assert wix.candle_exe == tmp_path / "tools" / "wix" / "candle.exe"


def test_download_wix(mock_command, tmp_path):
    """If there's no existing managed WiX install, it is downloaded and
    unpacked."""
    # Mock the environment as if there is not WiX variable
    mock_command.os.environ.get.return_value = None

    # Mock the download
    wix_path = tmp_path / "tools" / "wix"

    wix_zip_path = os.fsdecode(tmp_path / "tools" / "wix.zip")
    # Consider to remove if block when we drop py3.7 support, only keep statements from else.
    # MagicMock below py3.8 doesn't has __fspath__ attribute.
    if sys.version_info < (3, 8):
        wix_zip = FsPathMock(wix_zip_path)
    else:
        wix_zip = MagicMock()
        wix_zip.__fspath__.return_value = wix_zip_path

    mock_command.download_url.return_value = wix_zip

    # Verify the install. This will trigger a download
    wix = WiX.verify(mock_command)

    # The environment was queried.
    mock_command.os.environ.get.assert_called_with("WIX")

    # A download was initiated
    mock_command.download_url.assert_called_with(
        url=WIX_DOWNLOAD_URL,
        download_path=tmp_path / "tools",
    )

    # The download was unpacked.
    # TODO: Py3.6 compatibility; os.fsdecode not required in Py3.7
    mock_command.shutil.unpack_archive.assert_called_with(
        os.fsdecode(wix_zip_path), extract_dir=os.fsdecode(wix_path)
    )

    # The zip file was removed
    wix_zip.unlink.assert_called_with()

    # The returned paths are as expected
    assert wix.heat_exe == tmp_path / "tools" / "wix" / "heat.exe"
    assert wix.light_exe == tmp_path / "tools" / "wix" / "light.exe"
    assert wix.candle_exe == tmp_path / "tools" / "wix" / "candle.exe"


def test_dont_install(mock_command, tmp_path):
    """If there's no existing managed WiX install, an install is not requested,
    verify fails."""
    # Mock the environment as if there is not WiX variable
    mock_command.os.environ.get.return_value = None

    # Verify, but don't install. This will fail.
    with pytest.raises(MissingToolError):
        WiX.verify(mock_command, install=False)

    # The environment was queried.
    mock_command.os.environ.get.assert_called_with("WIX")

    # No download was initiated
    mock_command.download_url.assert_not_called()


def test_download_fail(mock_command, tmp_path):
    """If the download doesn't complete, the validator fails."""
    # Mock the environment as if there is not WiX variable
    mock_command.os.environ.get.return_value = None

    # Mock the download failure
    mock_command.download_url.side_effect = requests_exceptions.ConnectionError

    # Verify the install. This will trigger a download
    with pytest.raises(NetworkFailure):
        WiX.verify(mock_command)

    # The environment was queried.
    mock_command.os.environ.get.assert_called_with("WIX")

    # A download was initiated
    mock_command.download_url.assert_called_with(
        url=WIX_DOWNLOAD_URL,
        download_path=tmp_path / "tools",
    )

    # ... but the unpack didn't happen
    assert mock_command.shutil.unpack_archive.call_count == 0


def test_unpack_fail(mock_command, tmp_path):
    """If the download archive is corrupted, the validator fails."""
    # Mock the environment as if there is not WiX variable
    mock_command.os.environ.get.return_value = None

    # Mock the download
    wix_path = tmp_path / "tools" / "wix"

    wix_zip_path = os.fsdecode(tmp_path / "tools" / "wix.zip")
    # Consider to remove if block when we drop py3.7 support, only keep statements from else.
    # MagicMock below py3.8 doesn't has __fspath__ attribute.
    if sys.version_info < (3, 8):
        wix_zip = FsPathMock(wix_zip_path)
    else:
        wix_zip = MagicMock()
        wix_zip.__fspath__.return_value = wix_zip_path

    mock_command.download_url.return_value = wix_zip

    # Mock an unpack failure
    mock_command.shutil.unpack_archive.side_effect = EOFError

    # Verify the install. This will trigger a download,
    # but the unpack will fail
    with pytest.raises(BriefcaseCommandError, match="interrupted or corrupted"):
        WiX.verify(mock_command)

    # The environment was queried.
    mock_command.os.environ.get.assert_called_with("WIX")

    # A download was initiated
    mock_command.download_url.assert_called_with(
        url=WIX_DOWNLOAD_URL,
        download_path=tmp_path / "tools",
    )

    # The download was unpacked.
    # TODO: Py3.6 compatibility; os.fsdecode not required in Py3.7
    mock_command.shutil.unpack_archive.assert_called_with(
        os.fsdecode(wix_zip_path), extract_dir=os.fsdecode(wix_path)
    )

    # The zip file was not removed
    assert wix_zip.unlink.call_count == 0
