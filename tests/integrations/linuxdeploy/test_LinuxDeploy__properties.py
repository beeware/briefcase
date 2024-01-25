import pytest

from briefcase.exceptions import UnsupportedHostError
from briefcase.integrations.linuxdeploy import (
    LinuxDeploy,
    LinuxDeployGtkPlugin,
    LinuxDeployQtPlugin,
)

from ...utils import assert_url_resolvable


def test_managed_install(linuxdeploy):
    """All linuxdeploy installs are managed."""
    assert linuxdeploy.managed_install is True


def test_file_path(linuxdeploy, mock_tools):
    """Linuxdeploy resides in the tool path."""
    assert linuxdeploy.file_path == mock_tools.base_path


@pytest.mark.parametrize(
    "host_os, host_arch, is_32bit_python, linuxdeploy_arch",
    [
        ("Linux", "x86_64", False, "x86_64"),
        ("Linux", "x86_64", True, "i386"),
        ("Linux", "i686", True, "i386"),
        ("Linux", "aarch64", True, "armhf"),
        ("Linux", "aarch64", False, "aarch64"),
        ("Linux", "armv7l", True, "armhf"),
        ("Linux", "armv8l", True, "armhf"),
        ("Darwin", "x86_64", False, "x86_64"),
    ],
)
def test_file_name(mock_tools, host_os, host_arch, is_32bit_python, linuxdeploy_arch):
    """Linuxdeploy filename is architecture dependent."""
    mock_tools.host_os = host_os
    mock_tools.host_arch = host_arch
    mock_tools.is_32bit_python = is_32bit_python

    linuxdeploy = LinuxDeploy(mock_tools)

    assert linuxdeploy.file_name == f"linuxdeploy-{linuxdeploy_arch}.AppImage"


def test_file_name_unsupported_arch(mock_tools):
    """LinuxDeploy cannot be verified for an unsupported architecture."""
    mock_tools.host_arch = "IA-64"

    with pytest.raises(
        UnsupportedHostError,
        match="Linux AppImages cannot be built on IA-64.",
    ):
        _ = LinuxDeploy(mock_tools).file_name


@pytest.mark.parametrize(
    "host_os, host_arch, linuxdeploy_arch",
    [
        ("Linux", "x86_64", "x86_64"),
        ("Linux", "i686", "i386"),
        ("Darwin", "x86_64", "x86_64"),
    ],
)
def test_download_url(mock_tools, host_os, host_arch, linuxdeploy_arch):
    """Linuxdeploy download URL is architecture dependent."""
    mock_tools.host_os = host_os
    mock_tools.host_arch = host_arch

    linuxdeploy = LinuxDeploy(mock_tools)

    assert linuxdeploy.download_url == (
        "https://github.com/linuxdeploy/linuxdeploy/"
        f"releases/download/continuous/linuxdeploy-{linuxdeploy_arch}.AppImage"
    )
    assert_url_resolvable(linuxdeploy.download_url)


def test_plugins(linuxdeploy):
    """There are 2 known plugins."""
    assert linuxdeploy.plugins == {
        "gtk": LinuxDeployGtkPlugin,
        "qt": LinuxDeployQtPlugin,
    }
