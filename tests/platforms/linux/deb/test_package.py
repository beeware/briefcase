import subprocess
from unittest import mock

import pytest

from briefcase.console import Console, Log
from briefcase.exceptions import BriefcaseCommandError
from briefcase.platforms.linux import deb
from briefcase.platforms.linux.deb import LinuxDebPackageCommand


@pytest.fixture
def package_command(first_app, tmp_path):
    command = LinuxDebPackageCommand(
        logger=Log(),
        console=Console(),
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )
    command.tools.home_path = tmp_path / "home"

    # Set the host architecture for test purposes.
    command.tools.host_arch = "wonky"

    # Mock the app context
    command.tools.app_tools[first_app].app_context = mock.MagicMock()

    # Mock shutil
    command.tools.shutil = mock.MagicMock()

    return command


def test_verify_tools_docker(package_command):
    """If using Docker, no tool checks are needed"""
    package_command.target_image = "somevendor:surprising"
    package_command.tools.host_os = "Linux"

    # Verify the tools
    package_command.verify_tools()


def test_deb_build_tools(package_command, monkeypatch):
    """If we're on a Linux, and not using Docker, a check is made for the build tools"""
    package_command.target_image = None
    package_command.tools.host_os = "Linux"

    # Mock the existence of the debian_version file.
    dpkg_deb = mock.MagicMock()
    Path = mock.MagicMock(return_value=dpkg_deb)
    dpkg_deb.exists.return_value = True
    monkeypatch.setattr(deb, "Path", Path)

    # Verify the tools
    package_command.verify_tools()

    # The right path was checked
    Path.assert_called_once_with("/usr/bin/dpkg-deb")


def test_deb_build_tools_missing(package_command, monkeypatch):
    """If we're on a Linux, and not using Docker, and the deb build tools are mising, raise an error"""
    package_command.target_image = None
    package_command.tools.host_os = "Linux"

    # Mock the existence of the debian_version file.
    debian_version = mock.MagicMock()
    Path = mock.MagicMock(return_value=debian_version)
    debian_version.exists.return_value = False
    monkeypatch.setattr(deb, "Path", Path)

    # Verify the tools
    with pytest.raises(
        BriefcaseCommandError,
        match=r"Can't find the dpkg tools\. Try running `sudo apt install dpkg-dev`\.",
    ):
        package_command.verify_tools()

    # The right path was checked
    Path.assert_called_once_with("/usr/bin/dpkg-deb")


def test_package_app(package_command, first_app, tmp_path):
    """A deb app can be packaged."""
    # Package the app
    package_command.package_app(first_app, test_mode=False, passthrough=[])

    # The deb was built
    package_command.tools[first_app].app_context.run.assert_called_once_with(
        [
            "dpkg-deb",
            "--build",
            "--root-owner-group",
            "first-app_0.0.1-1_wonky",
        ],
        check=True,
        cwd=tmp_path
        / "base_path"
        / "linux"
        / "somevendor"
        / "surprising"
        / "system"
        / "First App",
    )

    # The deb was moved into the final location
    package_command.tools.shutil.move.assert_called_once_with(
        tmp_path
        / "base_path"
        / "linux"
        / "somevendor"
        / "surprising"
        / "system"
        / "First App"
        / "first-app_0.0.1-1_wonky.deb",
        tmp_path
        / "base_path"
        / "linux"
        / "first-app_0.0.1-1~somevendor-surprising_wonky.deb",
    )


def test_package_app_failure(package_command, first_app, tmp_path):
    """If the dpkg-deb call fails, an error is raised."""
    # Mock a build failure.
    package_command.tools[
        first_app
    ].app_context.run.side_effect = subprocess.CalledProcessError(
        cmd="dpkg-deb", returncode=-1
    )

    # Package the app; this will fail
    with pytest.raises(
        BriefcaseCommandError,
        match=r"Error while building .deb package for app first-app",
    ):
        package_command.package_app(first_app, test_mode=False)

    # An attempt to build deb was made
    package_command.tools[first_app].app_context.run.assert_called_once_with(
        [
            "dpkg-deb",
            "--build",
            "--root-owner-group",
            "first-app_0.0.1-1_wonky",
        ],
        check=True,
        cwd=tmp_path
        / "base_path"
        / "linux"
        / "somevendor"
        / "surprising"
        / "system"
        / "First App",
    )
