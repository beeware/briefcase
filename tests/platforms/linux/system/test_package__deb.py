import shutil
import subprocess
import sys
from pathlib import Path
from unittest import mock

import pytest

from briefcase.console import Console, Log
from briefcase.exceptions import BriefcaseCommandError
from briefcase.platforms.linux import system
from briefcase.platforms.linux.system import (
    LinuxSystemPackageCommand,
    debian_multiline_description,
)

from ....utils import create_file


@pytest.fixture
def package_command(first_app, tmp_path):
    command = LinuxSystemPackageCommand(
        logger=Log(),
        console=Console(),
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )
    command.tools.home_path = tmp_path / "home"

    # Mock ABI from packaging system
    command._deb_abi = "wonky"

    # Mock the app context
    command.tools.app_tools[first_app].app_context = mock.MagicMock()

    # Mock shutil
    command.tools.shutil = mock.MagicMock()
    # Make the mock rmtree still remove content
    command.tools.shutil.rmtree.side_effect = shutil.rmtree

    return command


@pytest.fixture
def first_app_deb(first_app):
    # Mock a debian app
    first_app.python_version_tag = "3.10"
    first_app.target_vendor_base = "debian"
    first_app.packaging_format = "deb"
    first_app.glibc_version = "2.99"
    first_app.long_description = "Long description\nfor the app"

    return first_app


def test_verify_no_docker(monkeypatch, package_command, first_app_deb):
    """If not using docker, existence of dpkg-deb is verified."""
    # Mock not using docker
    package_command.target_image = None

    # Mock the existence of dpkg-deb
    package_command.tools.shutil.which = mock.MagicMock(return_value="/mybin/dpkg-deb")

    # App tools can be verified
    package_command.verify_app_tools(first_app_deb)

    # dpkg_deb was inspected
    package_command.tools.shutil.which.assert_called_once_with("dpkg-deb")


@pytest.mark.parametrize(
    "vendor_base, error_msg",
    [
        (
            "debian",
            "Can't find the dpkg tools. Try running `sudo apt install dpkg-dev`.",
        ),
        (None, "Can't find the dpkg-deb tool. Install this first to package the deb."),
    ],
)
def test_verify_dpkg_deb_missing(
    monkeypatch,
    package_command,
    first_app_deb,
    vendor_base,
    error_msg,
):
    """If dpkg-deb isn't installed, an error is raised."""
    # Mock distro so packager is found or not appropriately
    first_app_deb.target_vendor_base = vendor_base

    # Mock packager as missing
    package_command.tools.shutil.which = mock.MagicMock(return_value="")

    # Mock not using docker
    package_command.target_image = None

    # Verifying app tools will raise an error
    with pytest.raises(BriefcaseCommandError, match=error_msg):
        package_command.verify_app_tools(first_app_deb)

    # which was called for dpkg-deb
    package_command.tools.shutil.which.assert_called_once_with("dpkg-deb")


def test_verify_docker(monkeypatch, package_command, first_app_deb):
    """If using Docker, no tool checks are needed."""
    # Mock using docker
    package_command.target_image = "somevendor:surprising"

    # Mock the existence of a valid non-docker system Python
    # with the same major/minor as the current Python,
    # plus the existence of dpkg-deb
    python3 = mock.MagicMock()
    python3.resolve.return_value = Path(
        f"/usr/bin/python{sys.version_info.major}.{sys.version_info.minor}"
    )

    dpkg_deb = mock.MagicMock()
    dpkg_deb.exists.return_value = False

    mock_Path = mock.MagicMock(side_effect=[python3, dpkg_deb])
    monkeypatch.setattr(system, "Path", mock_Path)

    # App tools can be verified
    package_command.verify_app_tools(first_app_deb)

    # dpkg_deb was not inspected
    dpkg_deb.exists.assert_not_called()


@pytest.mark.skipif(sys.platform == "win32", reason="Can't build debs on Windows")
def test_deb_package(package_command, first_app_deb, tmp_path):
    """A deb app can be packaged."""
    bundle_path = tmp_path / "base_path/build/first-app/somevendor/surprising"

    # Package the app
    package_command.package_app(first_app_deb)

    # The control file is written
    assert (bundle_path / "first-app-0.0.1/DEBIAN/control").exists()
    with (bundle_path / "first-app-0.0.1/DEBIAN/control").open(encoding="utf-8") as f:
        assert (
            f.read()
            == "\n".join(
                [
                    "Package: first-app",
                    "Version: 0.0.1",
                    "Architecture: wonky",
                    "Maintainer: Megacorp <maintainer@example.com>",
                    "Homepage: https://example.com/first-app",
                    "Description: The first simple app \\ demonstration",
                    " Long description",
                    " for the app",
                    "Depends: libc6 (>=2.99), libpython3.10",
                    "Section: utils",
                    "Priority: optional",
                ]
            )
            + "\n"
        )

    package_command.tools.app_tools[
        first_app_deb
    ].app_context.run.assert_called_once_with(
        [
            "dpkg-deb",
            "--build",
            "--root-owner-group",
            "first-app-0.0.1",
        ],
        check=True,
        cwd=bundle_path,
    )

    # The deb was moved into the final location
    package_command.tools.shutil.move.assert_called_once_with(
        bundle_path / "first-app-0.0.1.deb",
        tmp_path
        / "base_path"
        / "dist"
        / "first-app_0.0.1-1~somevendor-surprising_wonky.deb",
    )


def test_deb_re_package(package_command, first_app_deb, tmp_path):
    """A deb app that has previously been packaged can be re-packaged."""
    bundle_path = tmp_path / "base_path/build/first-app/somevendor/surprising"

    # Create an old control file that will be overwritten.
    create_file(bundle_path / "first-app-0.0.1/DEBIAN/control", "Old control content")

    # Package the app
    package_command.package_app(first_app_deb)

    # The control file is re-written
    assert (bundle_path / "first-app-0.0.1/DEBIAN/control").exists()
    with (bundle_path / "first-app-0.0.1/DEBIAN/control").open(encoding="utf-8") as f:
        assert (
            f.read()
            == "\n".join(
                [
                    "Package: first-app",
                    "Version: 0.0.1",
                    "Architecture: wonky",
                    "Maintainer: Megacorp <maintainer@example.com>",
                    "Homepage: https://example.com/first-app",
                    "Description: The first simple app \\ demonstration",
                    " Long description",
                    " for the app",
                    "Depends: libc6 (>=2.99), libpython3.10",
                    "Section: utils",
                    "Priority: optional",
                ]
            )
            + "\n"
        )

    package_command.tools.app_tools[
        first_app_deb
    ].app_context.run.assert_called_once_with(
        [
            "dpkg-deb",
            "--build",
            "--root-owner-group",
            "first-app-0.0.1",
        ],
        check=True,
        cwd=bundle_path,
    )

    # The deb was moved into the final location
    package_command.tools.shutil.move.assert_called_once_with(
        bundle_path / "first-app-0.0.1.deb",
        tmp_path
        / "base_path"
        / "dist"
        / "first-app_0.0.1-1~somevendor-surprising_wonky.deb",
    )


def test_deb_package_no_long_description(package_command, first_app_deb, tmp_path):
    """A deb app without a long description raises an error."""
    bundle_path = tmp_path / "base_path/build/first-app/somevendor/surprising"

    # Delete the long description
    first_app_deb.long_description = None

    # Packaging the app will fail
    with pytest.raises(
        BriefcaseCommandError,
        match=r"App configuration does not define `long_description`. Debian projects require a long description.",
    ):
        package_command.package_app(first_app_deb)

    # The control file won't be written
    assert not (bundle_path / "first-app-0.0.1/DEBIAN/control").exists()


@pytest.mark.parametrize(
    "input, output",
    [
        ["", ""],
        ["one line", "one line"],
        ["first line\nsecond line", "first line\n second line"],
        ["first line\n\nsecond line", "first line\n second line"],
        ["first line\n  \nsecond line", "first line\n second line"],
    ],
)
def test_multiline_long_description(input, output):
    """Multiline debian descriptions are transformed."""
    assert debian_multiline_description(input) == output


def test_deb_package_extra_requirements(package_command, first_app_deb, tmp_path):
    """A deb app can be packaged with extra runtime requirements and configuration
    options."""
    bundle_path = tmp_path / "base_path/build/first-app/somevendor/surprising"

    # Add system requirements and other optional settings.
    first_app_deb.system_runtime_requires = ["first", "second (>=1.2.3)"]
    first_app_deb.revision = 42
    first_app_deb.system_section = "Funny stuff"

    # Package the app
    package_command.package_app(first_app_deb)

    # The control file is written
    assert (bundle_path / "first-app-0.0.1/DEBIAN/control").exists()
    with (bundle_path / "first-app-0.0.1/DEBIAN/control").open(encoding="utf-8") as f:
        assert (
            f.read()
            == "\n".join(
                [
                    "Package: first-app",
                    "Version: 0.0.1",
                    "Architecture: wonky",
                    "Maintainer: Megacorp <maintainer@example.com>",
                    "Homepage: https://example.com/first-app",
                    "Description: The first simple app \\ demonstration",
                    " Long description",
                    " for the app",
                    "Depends: libc6 (>=2.99), libpython3.10, first, second (>=1.2.3)",
                    "Section: Funny stuff",
                    "Priority: optional",
                ]
            )
            + "\n"
        )

    package_command.tools.app_tools[
        first_app_deb
    ].app_context.run.assert_called_once_with(
        [
            "dpkg-deb",
            "--build",
            "--root-owner-group",
            "first-app-0.0.1",
        ],
        check=True,
        cwd=bundle_path,
    )

    # The deb was moved into the final location
    package_command.tools.shutil.move.assert_called_once_with(
        bundle_path / "first-app-0.0.1.deb",
        tmp_path
        / "base_path"
        / "dist"
        / "first-app_0.0.1-42~somevendor-surprising_wonky.deb",
    )


def test_deb_package_failure(package_command, first_app_deb, tmp_path):
    """If a packaging doesn't succeed, an error is raised."""
    bundle_path = tmp_path / "base_path/build/first-app/somevendor/surprising"

    # Mock a packaging failure
    package_command.tools.app_tools[first_app_deb].app_context.run.side_effect = (
        subprocess.CalledProcessError(cmd="dpkg-deb ...", returncode=-1)
    )

    # Package the app
    with pytest.raises(
        BriefcaseCommandError, match=r"Error while building .deb package for first-app."
    ):
        package_command.package_app(first_app_deb)

    # The control file is written
    assert (bundle_path / "first-app-0.0.1/DEBIAN/control").exists()
    with (bundle_path / "first-app-0.0.1/DEBIAN/control").open(encoding="utf-8") as f:
        assert (
            f.read()
            == "\n".join(
                [
                    "Package: first-app",
                    "Version: 0.0.1",
                    "Architecture: wonky",
                    "Maintainer: Megacorp <maintainer@example.com>",
                    "Homepage: https://example.com/first-app",
                    "Description: The first simple app \\ demonstration",
                    " Long description",
                    " for the app",
                    "Depends: libc6 (>=2.99), libpython3.10",
                    "Section: utils",
                    "Priority: optional",
                ]
            )
            + "\n"
        )

    # The call to package was made
    package_command.tools.app_tools[
        first_app_deb
    ].app_context.run.assert_called_once_with(
        [
            "dpkg-deb",
            "--build",
            "--root-owner-group",
            "first-app-0.0.1",
        ],
        check=True,
        cwd=bundle_path,
    )

    # The deb wasn't built, so it wasn't moved.
    package_command.tools.shutil.move.assert_not_called()
