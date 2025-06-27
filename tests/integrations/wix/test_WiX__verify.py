from subprocess import CalledProcessError
from unittest.mock import MagicMock

import pytest

from briefcase.exceptions import (
    BriefcaseCommandError,
    MissingToolError,
    NetworkFailure,
    UnsupportedHostError,
)
from briefcase.integrations.wix import WiX

from ...utils import assert_url_resolvable
from .conftest import WIX_DOWNLOAD_URL, WIX_EXE_PATH


def test_short_circuit(mock_tools):
    """Tool is not created if already cached."""
    mock_tools.wix = "tool"

    tool = WiX.verify(mock_tools)

    assert tool == "tool"
    assert tool == mock_tools.wix


@pytest.mark.parametrize("host_os", ["Darwin", "Linux", "wonky"])
def test_unsupported_os(mock_tools, host_os):
    """When host OS is not supported, an error is raised."""
    mock_tools.host_os = host_os

    with pytest.raises(
        UnsupportedHostError,
        match=f"{WiX.name} is not supported on {host_os}",
    ):
        WiX.verify(mock_tools)


def test_existing_wix_install(mock_tools, wix_path):
    """If there's an existing managed WiX install, the validator succeeds."""
    # Create a mock of a previously installed WiX version.
    wix_exe = wix_path / WIX_EXE_PATH
    wix_exe.parent.mkdir(parents=True)
    wix_exe.touch()

    mock_tools.subprocess.check_output.return_value = "5.0.2+aa65968c"

    wix = WiX.verify(mock_tools)

    # Version was checked
    mock_tools.subprocess.check_output.assert_called_once_with([wix_exe, "--version"])

    # No download was attempted
    assert mock_tools.file.download.call_count == 0

    # The returned paths are as expected
    assert wix.wix_exe == wix_exe


def test_download_missing(capsys, mock_tools, wix_path):
    """If there's no existing managed WiX install, it is downloaded and unpacked."""
    assert_download(mock_tools, wix_path)
    assert "WiX toolset was not found" in capsys.readouterr().out

    # Version was not checked
    mock_tools.subprocess.check_output.assert_not_called()

    # The WiX URL is resolvable
    assert_url_resolvable(WiX.verify(mock_tools).download_url)


@pytest.mark.parametrize(
    "exc",
    [PermissionError(), CalledProcessError(1, "wix")],
)
def test_download_unusable(capsys, mock_tools, wix_path, exc):
    """If the existing managed WiX install is unusable, it is reinstalled."""
    wix_exe = wix_path / WIX_EXE_PATH
    wix_exe.parent.mkdir(parents=True)
    wix_exe.touch()

    mock_tools.subprocess.check_output.side_effect = exc

    assert_download(mock_tools, wix_path)
    assert (
        f"WiX toolset is unusable ({type(exc).__name__}: {exc})"
        in capsys.readouterr().out
    )

    # Version was checked
    mock_tools.subprocess.check_output.assert_called_once_with([wix_exe, "--version"])


def test_download_version(capsys, mock_tools, wix_path):
    """If the existing managed WiX install is the wrong version, it is reinstalled."""
    wix_exe = wix_path / WIX_EXE_PATH
    wix_exe.parent.mkdir(parents=True)
    wix_exe.touch()

    mock_tools.subprocess.check_output.return_value = "5.0.1"

    assert_download(mock_tools, wix_path)
    assert "WiX toolset is an unsupported version (5.0.1)" in capsys.readouterr().out

    # Version was checked
    mock_tools.subprocess.check_output.assert_called_once_with([wix_exe, "--version"])


def assert_download(mock_tools, wix_path):
    # Mock the download
    wix_msi_path = wix_path.parent / "wix.msi"
    wix_msi_path.touch()
    mock_tools.file.download = MagicMock(return_value=wix_msi_path)

    # Verify the install. This will trigger a download
    wix = WiX.verify(mock_tools)

    # A download was initiated
    mock_tools.file.download.assert_called_with(
        url=WIX_DOWNLOAD_URL,
        download_path=wix_path.parent,
        role="WiX",
    )

    # The download was unpacked.
    mock_tools.subprocess.run.assert_called_with(
        ["msiexec", "/a", wix_msi_path, "/qn", f"TARGETDIR={wix_path}"], check=True
    )

    # The msi file was removed
    assert not wix_msi_path.exists()

    # The returned paths are as expected
    assert wix.wix_exe == wix_path / WIX_EXE_PATH


def test_dont_install(mock_tools, tmp_path):
    """If there's no existing managed WiX install, and install is not requested, verify
    fails."""
    # Verify, but don't install. This will fail.
    with pytest.raises(MissingToolError):
        WiX.verify(mock_tools, install=False)

    # No download was initiated
    mock_tools.file.download.assert_not_called()


def test_download_fail(mock_tools, tmp_path):
    """If the download doesn't complete, the validator fails."""
    # Mock the download failure
    mock_tools.file.download = MagicMock(side_effect=NetworkFailure("mock"))

    # Verify the install. This will trigger a download
    with pytest.raises(NetworkFailure, match="Unable to mock"):
        WiX.verify(mock_tools)

    # A download was initiated
    mock_tools.file.download.assert_called_with(
        url=WIX_DOWNLOAD_URL,
        download_path=tmp_path / "tools",
        role="WiX",
    )

    # ... but the unpack didn't happen
    mock_tools.subprocess.run.assert_not_called()


def test_unpack_fail(capsys, mock_tools, wix_path):
    """If the download archive is corrupted, the validator fails."""
    # Mock the download
    wix_msi_path = wix_path.parent / "wix.msi"
    wix_msi_path.touch()
    mock_tools.file.download = MagicMock(return_value=wix_msi_path)

    # Mock an msiexec failure
    mock_tools.subprocess.run.side_effect = CalledProcessError(1, "msiexec")

    # Verify the install. This will trigger a download,
    # but the unpack will fail
    with pytest.raises(BriefcaseCommandError, match="interrupted or corrupted"):
        WiX.verify(mock_tools)

    # A download was initiated
    mock_tools.file.download.assert_called_with(
        url=WIX_DOWNLOAD_URL,
        download_path=wix_path.parent,
        role="WiX",
    )

    # The download was unpacked.
    mock_tools.subprocess.run.assert_called_with(
        ["msiexec", "/a", wix_msi_path, "/qn", f"TARGETDIR={wix_path}"], check=True
    )

    # The zip file was not removed
    assert wix_msi_path.exists()
