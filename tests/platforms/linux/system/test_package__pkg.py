import shutil
import subprocess
import sys
import tarfile
from pathlib import Path
from unittest import mock

import pytest

from briefcase.console import Console, Log
from briefcase.exceptions import BriefcaseCommandError
from briefcase.platforms.linux import system
from briefcase.platforms.linux.system import LinuxSystemPackageCommand

from ....utils import create_file, create_tgz_file


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
    command._pkg_abi = "wonky"

    # Mock the app context
    command.tools.app_tools[first_app].app_context = mock.MagicMock()

    # Mock shutil
    command.tools.shutil = mock.MagicMock()

    # Make the mock copy still copy
    command.tools.shutil.copy = mock.MagicMock(side_effect=shutil.copy)

    # Make the mock make_archive still package tarballs
    command.tools.shutil.make_archive = mock.MagicMock(side_effect=shutil.make_archive)

    # Make the mock rmtree still remove content
    command.tools.shutil.rmtree = mock.MagicMock(side_effect=shutil.rmtree)

    return command


@pytest.fixture
def first_app_pkg(first_app, tmp_path):
    # Mock an Arch app
    first_app.python_version_tag = "3.10"
    first_app.target_vendor_base = "arch"
    first_app.packaging_format = "pkg"
    first_app.glibc_version = "2.99"
    first_app.description = "Description for the app"
    first_app.license = "BSD License"

    # Mock the side effects of building the app
    usr_dir = (
        tmp_path
        / "base_path"
        / "build"
        / "first-app"
        / "somevendor"
        / "surprising"
        / "first-app-0.0.1"
        / "usr"
    )

    # Create the binary
    create_file(usr_dir / "bin/first-app", "binary")

    # Files in an app-named folder
    create_file(usr_dir / "share/doc/first-app/license", "license")
    create_file(usr_dir / "share/doc/first-app/UserManual", "manual")

    # A share file in an app-named folder
    create_file(usr_dir / "share/man/man1/first-app.1.gz", "man")

    return first_app


def test_verify_no_docker(monkeypatch, package_command, first_app_pkg):
    """If not using docker, existence of makepkg is verified."""
    # Mock not using docker
    package_command.target_image = None

    # Mock the existence of makepkg
    package_command.tools.shutil.which = mock.MagicMock(return_value="/mybin/makepkg")

    # App tools can be verified
    package_command.verify_app_tools(first_app_pkg)

    # makepkg was inspected
    package_command.tools.shutil.which.assert_called_once_with("makepkg")


@pytest.mark.parametrize(
    "vendor_base, error_msg",
    [
        (
            "arch",
            "Can't find the makepkg tools. Try running `sudo pacman -Syu pacman`.",
        ),
        (None, "Can't find the makepkg tool. Install this first to package the pkg."),
    ],
)
def test_verify_makepkg_missing(
    monkeypatch,
    package_command,
    first_app_pkg,
    vendor_base,
    error_msg,
):
    """If makepkg isn't installed, an error is raised."""
    # Mock distro so packager is found or not appropriately
    first_app_pkg.target_vendor_base = vendor_base

    # Mock packager as missing
    package_command.tools.shutil.which = mock.MagicMock(return_value="")

    # Mock not using docker
    package_command.target_image = None

    # Verifying app tools will raise an error
    with pytest.raises(BriefcaseCommandError, match=error_msg):
        package_command.verify_app_tools(first_app_pkg)

    # which was called for makepkg
    package_command.tools.shutil.which.assert_called_once_with("makepkg")


def test_verify_docker(monkeypatch, package_command, first_app_pkg):
    """If using Docker, no tool checks are needed."""
    # Mock using docker
    package_command.target_image = "somevendor:surprising"

    # Mock the existence of a valid non-docker system Python
    # with the same major/minor as the current Python,
    # plus the existence of makepkg
    python3 = mock.MagicMock()
    python3.resolve.return_value = Path(
        f"/usr/bin/python{sys.version_info.major}.{sys.version_info.minor}"
    )

    makepkg = mock.MagicMock()
    makepkg.exists.return_value = False

    mock_Path = mock.MagicMock(side_effect=[python3, makepkg])
    monkeypatch.setattr(system, "Path", mock_Path)

    # App tools can be verified
    package_command.verify_app_tools(first_app_pkg)

    # makepkg was not inspected
    makepkg.exists.assert_not_called()


@pytest.mark.skipif(sys.platform == "win32", reason="Can't build PKGs on Windows")
def test_pkg_package(package_command, first_app_pkg, tmp_path):
    """A pkg app can be packaged."""
    bundle_path = tmp_path / "base_path/build/first-app/somevendor/surprising"

    # Package the app
    package_command.package_app(first_app_pkg)

    # The CHANGELOG file is copied
    assert (bundle_path / "pkgbuild/CHANGELOG").exists()

    # The PKGBUILD file is written
    assert (bundle_path / "pkgbuild/PKGBUILD").exists()
    with (bundle_path / "pkgbuild/PKGBUILD").open(encoding="utf-8") as f:
        assert f.read() == "\n".join(
            [
                "# Maintainer: Megacorp <maintainer@example.com>",
                'export PACKAGER="Megacorp <maintainer@example.com>"',
                "pkgname=first-app",
                "pkgver=0.0.1",
                "pkgrel=1",
                'pkgdesc="Description for the app"',
                "arch=('wonky')",
                'url="https://example.com/first-app"',
                "license=('BSD License')",
                "depends=('glibc>=2.99' 'python3')",
                "changelog=CHANGELOG",
                'source=("$pkgname-$pkgver.tar.gz")',
                "md5sums=('SKIP')",
                "options=('!strip')",
                "package() {",
                '    cp -r "$srcdir/$pkgname-$pkgver/usr/" "$pkgdir"/usr/',
                "}",
            ]
        )

    # A source tarball was created with the right content
    archive_file = bundle_path / "pkgbuild/first-app-0.0.1.tar.gz"
    assert archive_file.exists()
    with tarfile.open(archive_file, "r:gz") as archive:
        assert sorted(archive.getnames()) == [
            "first-app-0.0.1",
            "first-app-0.0.1/usr",
            "first-app-0.0.1/usr/bin",
            "first-app-0.0.1/usr/bin/first-app",
            "first-app-0.0.1/usr/lib",
            "first-app-0.0.1/usr/lib/first-app",
            "first-app-0.0.1/usr/lib/first-app/app",
            "first-app-0.0.1/usr/lib/first-app/app/support.so",
            "first-app-0.0.1/usr/lib/first-app/app/support_same_perms.so",
            "first-app-0.0.1/usr/lib/first-app/app_packages",
            "first-app-0.0.1/usr/lib/first-app/app_packages/firstlib",
            "first-app-0.0.1/usr/lib/first-app/app_packages/firstlib/first.so",
            "first-app-0.0.1/usr/lib/first-app/app_packages/firstlib/first.so.1.0",
            "first-app-0.0.1/usr/lib/first-app/app_packages/secondlib",
            "first-app-0.0.1/usr/lib/first-app/app_packages/secondlib/second_a.so",
            "first-app-0.0.1/usr/lib/first-app/app_packages/secondlib/second_b.so",
            "first-app-0.0.1/usr/share",
            "first-app-0.0.1/usr/share/doc",
            "first-app-0.0.1/usr/share/doc/first-app",
            "first-app-0.0.1/usr/share/doc/first-app/UserManual",
            "first-app-0.0.1/usr/share/doc/first-app/license",
            "first-app-0.0.1/usr/share/man",
            "first-app-0.0.1/usr/share/man/man1",
            "first-app-0.0.1/usr/share/man/man1/first-app.1.gz",
        ]

    # makepkg was invoked
    package_command.tools.app_tools[
        first_app_pkg
    ].app_context.run.assert_called_once_with(
        [
            "makepkg",
        ],
        check=True,
        cwd=(bundle_path / "pkgbuild"),
        env={"PKGEXT": ".pkg.tar.zst"},
    )

    # The pkg was moved into the final location
    package_command.tools.shutil.move.assert_called_once_with(
        bundle_path / "pkgbuild/first-app-0.0.1-1-wonky.pkg.tar.zst",
        tmp_path / "base_path/dist/first-app-0.0.1-1-wonky.pkg.tar.zst",
    )


@pytest.mark.skipif(sys.platform == "win32", reason="Can't build PKGs on Windows")
def test_pkg_re_package(package_command, first_app_pkg, tmp_path):
    """A pkg app that has previously been packaged can be re-packaged."""
    bundle_path = tmp_path / "base_path/build/first-app/somevendor/surprising"

    # Create an old PKGBUILD file and tarball that will be overwritten.
    create_file(
        bundle_path / "pkgbuild/PKGBUILD",
        "Old PKGBUILD content",
    )
    create_tgz_file(
        bundle_path / "pkgbuild/first-app-0.0.1.tar.gz",
        [("old.txt", "old content")],
    )

    # Package the app
    package_command.package_app(first_app_pkg)

    # The CHANGELOG file is copied
    assert (bundle_path / "pkgbuild/CHANGELOG").exists()

    # The PKGBUILD file is written
    assert (bundle_path / "pkgbuild/PKGBUILD").exists()
    with (bundle_path / "pkgbuild/PKGBUILD").open(encoding="utf-8") as f:
        assert f.read() == "\n".join(
            [
                "# Maintainer: Megacorp <maintainer@example.com>",
                'export PACKAGER="Megacorp <maintainer@example.com>"',
                "pkgname=first-app",
                "pkgver=0.0.1",
                "pkgrel=1",
                'pkgdesc="Description for the app"',
                "arch=('wonky')",
                'url="https://example.com/first-app"',
                "license=('BSD License')",
                "depends=('glibc>=2.99' 'python3')",
                "changelog=CHANGELOG",
                'source=("$pkgname-$pkgver.tar.gz")',
                "md5sums=('SKIP')",
                "options=('!strip')",
                "package() {",
                '    cp -r "$srcdir/$pkgname-$pkgver/usr/" "$pkgdir"/usr/',
                "}",
            ]
        )

    # A source tarball was created with the right content
    archive_file = bundle_path / "pkgbuild/first-app-0.0.1.tar.gz"
    assert archive_file.exists()
    with tarfile.open(archive_file, "r:gz") as archive:
        assert sorted(archive.getnames()) == [
            "first-app-0.0.1",
            "first-app-0.0.1/usr",
            "first-app-0.0.1/usr/bin",
            "first-app-0.0.1/usr/bin/first-app",
            "first-app-0.0.1/usr/lib",
            "first-app-0.0.1/usr/lib/first-app",
            "first-app-0.0.1/usr/lib/first-app/app",
            "first-app-0.0.1/usr/lib/first-app/app/support.so",
            "first-app-0.0.1/usr/lib/first-app/app/support_same_perms.so",
            "first-app-0.0.1/usr/lib/first-app/app_packages",
            "first-app-0.0.1/usr/lib/first-app/app_packages/firstlib",
            "first-app-0.0.1/usr/lib/first-app/app_packages/firstlib/first.so",
            "first-app-0.0.1/usr/lib/first-app/app_packages/firstlib/first.so.1.0",
            "first-app-0.0.1/usr/lib/first-app/app_packages/secondlib",
            "first-app-0.0.1/usr/lib/first-app/app_packages/secondlib/second_a.so",
            "first-app-0.0.1/usr/lib/first-app/app_packages/secondlib/second_b.so",
            "first-app-0.0.1/usr/share",
            "first-app-0.0.1/usr/share/doc",
            "first-app-0.0.1/usr/share/doc/first-app",
            "first-app-0.0.1/usr/share/doc/first-app/UserManual",
            "first-app-0.0.1/usr/share/doc/first-app/license",
            "first-app-0.0.1/usr/share/man",
            "first-app-0.0.1/usr/share/man/man1",
            "first-app-0.0.1/usr/share/man/man1/first-app.1.gz",
        ]

    # makepkg was invoked
    package_command.tools.app_tools[
        first_app_pkg
    ].app_context.run.assert_called_once_with(
        [
            "makepkg",
        ],
        check=True,
        cwd=(bundle_path / "pkgbuild"),
        env={"PKGEXT": ".pkg.tar.zst"},
    )

    # The pkg was moved into the final location
    package_command.tools.shutil.move.assert_called_once_with(
        bundle_path / "pkgbuild/first-app-0.0.1-1-wonky.pkg.tar.zst",
        tmp_path / "base_path/dist/first-app-0.0.1-1-wonky.pkg.tar.zst",
    )


@pytest.mark.skipif(sys.platform == "win32", reason="Can't build PKGs on Windows")
def test_pkg_package_no_description(package_command, first_app_pkg, tmp_path):
    """A pkg app without a description raises an error."""
    bundle_path = tmp_path / "base_path/build/first-app/somevendor/surprising"

    # Delete the long description
    first_app_pkg.description = None

    # Packaging the app will fail
    with pytest.raises(
        BriefcaseCommandError,
        match=r"App configuration does not define `description`. Arch projects require a description.",
    ):
        package_command.package_app(first_app_pkg)

    # The CHANGELOG file, PKGBUILD file and tarball won't be written
    assert not (bundle_path / "pkgbuild/CHANGELOG").exists()
    assert not (bundle_path / "pkgbuild/PKGBUILD").exists()
    assert not (bundle_path / "pkgbuild/first-app-0.0.1.tar.gz").exists()


@pytest.mark.skipif(sys.platform == "win32", reason="Can't build PKGs on Windows")
def test_pkg_package_extra_requirements(package_command, first_app_pkg, tmp_path):
    """A pkg app can be packaged with extra runtime requirements and config features."""
    bundle_path = tmp_path / "base_path/build/first-app/somevendor/surprising"

    # Add system requirements and other optional settings.
    first_app_pkg.system_runtime_requires = ["first", "second"]
    first_app_pkg.revision = 1
    first_app_pkg.license = "BSD License"

    # Package the app
    package_command.package_app(first_app_pkg)

    # The CHANGELOG file is copied
    assert (bundle_path / "pkgbuild/CHANGELOG").exists()

    # The PKGBUILD file is written
    assert (bundle_path / "pkgbuild/PKGBUILD").exists()
    with (bundle_path / "pkgbuild/PKGBUILD").open(encoding="utf-8") as f:
        assert f.read() == "\n".join(
            [
                "# Maintainer: Megacorp <maintainer@example.com>",
                'export PACKAGER="Megacorp <maintainer@example.com>"',
                "pkgname=first-app",
                "pkgver=0.0.1",
                "pkgrel=1",
                'pkgdesc="Description for the app"',
                "arch=('wonky')",
                'url="https://example.com/first-app"',
                "license=('BSD License')",
                "depends=('glibc>=2.99' 'python3' 'first' 'second')",
                "changelog=CHANGELOG",
                'source=("$pkgname-$pkgver.tar.gz")',
                "md5sums=('SKIP')",
                "options=('!strip')",
                "package() {",
                '    cp -r "$srcdir/$pkgname-$pkgver/usr/" "$pkgdir"/usr/',
                "}",
            ]
        )

    # A source tarball was created
    archive_file = bundle_path / "pkgbuild/first-app-0.0.1.tar.gz"
    assert archive_file.exists()

    # makepkg was invoked
    package_command.tools.app_tools[
        first_app_pkg
    ].app_context.run.assert_called_once_with(
        [
            "makepkg",
        ],
        check=True,
        cwd=(bundle_path / "pkgbuild"),
        env={"PKGEXT": ".pkg.tar.zst"},
    )

    # The pkg was moved into the final location
    package_command.tools.shutil.move.assert_called_once_with(
        bundle_path / "pkgbuild/first-app-0.0.1-1-wonky.pkg.tar.zst",
        tmp_path / "base_path/dist/first-app-0.0.1-1-wonky.pkg.tar.zst",
    )


@pytest.mark.skipif(sys.platform == "win32", reason="Can't build PKGs on Windows")
def test_pkg_package_failure(package_command, first_app_pkg, tmp_path):
    """If a packaging doesn't succeed, an error is raised."""
    bundle_path = tmp_path / "base_path/build/first-app/somevendor/surprising"

    # Mock a packaging failure
    package_command.tools.app_tools[first_app_pkg].app_context.run.side_effect = (
        subprocess.CalledProcessError(cmd="makepkg ...", returncode=-1)
    )

    # Package the app; this will fail
    with pytest.raises(
        BriefcaseCommandError,
        match=r"Error while building .pkg.tar.zst package for first-app.",
    ):
        package_command.package_app(first_app_pkg)

    # The CHANGELOG file is copied
    assert (bundle_path / "pkgbuild/CHANGELOG").exists()

    # The PKGBUILD file is written
    assert (bundle_path / "pkgbuild/PKGBUILD").exists()

    # A source tarball was created
    archive_file = bundle_path / "pkgbuild/first-app-0.0.1.tar.gz"
    assert archive_file.exists()

    # makepkg was invoked
    package_command.tools.app_tools[
        first_app_pkg
    ].app_context.run.assert_called_once_with(
        [
            "makepkg",
        ],
        check=True,
        cwd=(bundle_path / "pkgbuild"),
        env={"PKGEXT": ".pkg.tar.zst"},
    )

    # The pkg wasn't built, so it wasn't moved.
    package_command.tools.shutil.move.assert_not_called()


@pytest.mark.skipif(sys.platform == "win32", reason="Can't build PKGs on Windows")
def test_no_changelog(package_command, first_app_pkg, tmp_path):
    """If a packaging doesn't succeed, an error is raised."""
    bundle_path = tmp_path / "base_path/build/first-app/somevendor/surprising"

    # Remove the changelog file
    (tmp_path / "base_path/CHANGELOG").unlink()

    # Package the app; this will fail
    with pytest.raises(
        BriefcaseCommandError, match=r"Your project does not contain a CHANGELOG file."
    ):
        package_command.package_app(first_app_pkg)

    # The CHANGELOG file will not be copied
    assert not (bundle_path / "pkgbuild/CHANGELOG").exists()

    # The PKGBUILD file will not exist (as existence of changelog is checked before writing the PKGBUILD file)
    assert not (bundle_path / "pkgbuild/PKGBUILD").exists()

    # No source tarball was created
    archive_file = bundle_path / "pkgbuild/first-app-0.0.1.tar.gz"
    assert not archive_file.exists()

    # makepkg wasn't invoked
    package_command.tools.app_tools[first_app_pkg].app_context.run.assert_not_called()

    # The pkg wasn't built, so it wasn't moved.
    package_command.tools.shutil.move.assert_not_called()
