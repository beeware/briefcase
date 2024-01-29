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
    command._rpm_abi = "wonky"

    # Mock the app context
    command.tools.app_tools[first_app].app_context = mock.MagicMock()

    # Mock shutil
    command.tools.shutil = mock.MagicMock()

    # Make the mock make_archive still package tarballs
    command.tools.shutil.make_archive = mock.MagicMock(side_effect=shutil.make_archive)

    # Make the mock rmtree still remove content
    command.tools.shutil.rmtree = mock.MagicMock(side_effect=shutil.rmtree)

    # Mock the RPM tag, since "somevendor" won't identify as rpm.
    command.rpm_tag = mock.MagicMock(return_value="fcXX")
    return command


@pytest.fixture
def first_app_rpm(first_app, tmp_path):
    # Mock a Red Hat app
    first_app.python_version_tag = "3"
    first_app.target_vendor_base = "rhel"
    first_app.packaging_format = "rpm"
    first_app.glibc_version = "2.99"
    first_app.long_description = "Long description\nfor the app"

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


def test_verify_no_docker(monkeypatch, package_command, first_app_rpm):
    """If not using docker, existence of rpmbuild is verified."""
    # Mock not using docker
    package_command.target_image = None

    # Mock the existence of rpmbuild
    package_command.tools.shutil.which = mock.MagicMock(return_value="/mybin/rpmbuild")

    # App tools can be verified
    package_command.verify_app_tools(first_app_rpm)

    # rpmbuild was inspected
    package_command.tools.shutil.which.assert_called_once_with("rpmbuild")


@pytest.mark.parametrize(
    "vendor_base, error_msg",
    [
        (
            "rhel",
            "Can't find the rpm-build tools. Try running `sudo dnf install rpmbuild`.",
        ),
        (None, "Can't find the rpmbuild tool. Install this first to package the rpm."),
    ],
)
def test_verify_rpmbuild_missing(
    monkeypatch,
    package_command,
    first_app_rpm,
    vendor_base,
    error_msg,
):
    """If rpmbuild isn't installed, an error is raised."""
    # Mock distro so packager is found or not appropriately
    first_app_rpm.target_vendor_base = vendor_base

    # Mock packager as missing
    package_command.tools.shutil.which = mock.MagicMock(return_value="")

    # Mock not using docker
    package_command.target_image = None

    # Verifying app tools will raise an error
    with pytest.raises(BriefcaseCommandError, match=error_msg):
        package_command.verify_app_tools(first_app_rpm)

    # rpmbuild was inspected
    package_command.tools.shutil.which.assert_called_once_with("rpmbuild")


def test_verify_docker(monkeypatch, package_command, first_app_rpm):
    """If using Docker, no tool checks are needed."""
    # Mock using docker
    package_command.target_image = "somevendor:surprising"

    # Mock the existence of a valid non-docker system Python
    # with the same major/minor as the current Python,
    # plus the existence of rpmbuild
    python3 = mock.MagicMock()
    python3.resolve.return_value = Path(
        f"/usr/bin/python{sys.version_info.major}.{sys.version_info.minor}"
    )

    rpmbuild = mock.MagicMock()
    rpmbuild.exists.return_value = False

    mock_Path = mock.MagicMock(side_effect=[python3, rpmbuild])
    monkeypatch.setattr(system, "Path", mock_Path)

    # App tools can be verified
    package_command.verify_app_tools(first_app_rpm)

    # rpmbuild was not inspected
    rpmbuild.exists.assert_not_called()


@pytest.mark.skipif(sys.platform == "win32", reason="Can't build RPMs on Windows")
def test_rpm_package(package_command, first_app_rpm, tmp_path):
    """A rpm app can be packaged."""
    bundle_path = tmp_path / "base_path/build/first-app/somevendor/surprising"

    # Package the app
    package_command.package_app(first_app_rpm)

    # rpmbuild layout has been generated
    assert (bundle_path / "rpmbuild/BUILD").exists()
    assert (bundle_path / "rpmbuild/BUILDROOT").exists()
    assert (bundle_path / "rpmbuild/RPMS").exists()
    assert (bundle_path / "rpmbuild/SOURCES").exists()
    assert (bundle_path / "rpmbuild/SRPMS").exists()
    assert (bundle_path / "rpmbuild/SPECS").exists()

    # The spec file is written
    assert (bundle_path / "rpmbuild/SPECS/first-app.spec").exists()
    with (bundle_path / "rpmbuild/SPECS/first-app.spec").open(encoding="utf-8") as f:
        assert f.read() == "\n".join(
            [
                "%global __brp_mangle_shebangs %{nil}",
                "%global __brp_strip %{nil}",
                "%global __brp_strip_static_archive %{nil}",
                "%global __brp_strip_comment_note %{nil}",
                "%global __brp_check_rpaths %{nil}",
                "%global __requires_exclude_from ^%{_libdir}/first-app/.*$",
                "%global __provides_exclude_from ^%{_libdir}/first-app/.*$",
                "%global _enable_debug_package 0",
                "%global debug_package %{nil}",
                "",
                "Name:           first-app",
                "Version:        0.0.1",
                "Release:        1%{?dist}",
                "Summary:        The first simple app \\ demonstration",
                "",
                "License:        Unknown",
                "URL:            https://example.com/first-app",
                "Source0:        %{name}-%{version}.tar.gz",
                "",
                "Requires:       python3",
                "",
                "ExclusiveArch:  wonky",
                "",
                "%description",
                "Long description",
                "for the app",
                "",
                "%prep",
                "%autosetup",
                "",
                "%build",
                "",
                "%install",
                "cp -r usr %{buildroot}/usr",
                "",
                "%files",
                '"/usr/bin/first-app"',
                '%dir "/usr/lib/first-app"',
                '%dir "/usr/lib/first-app/app"',
                '"/usr/lib/first-app/app/support.so"',
                '"/usr/lib/first-app/app/support_same_perms.so"',
                '%dir "/usr/lib/first-app/app_packages"',
                '%dir "/usr/lib/first-app/app_packages/firstlib"',
                '"/usr/lib/first-app/app_packages/firstlib/first.so"',
                '"/usr/lib/first-app/app_packages/firstlib/first.so.1.0"',
                '%dir "/usr/lib/first-app/app_packages/secondlib"',
                '"/usr/lib/first-app/app_packages/secondlib/second_a.so"',
                '"/usr/lib/first-app/app_packages/secondlib/second_b.so"',
                '%dir "/usr/share/doc/first-app"',
                '"/usr/share/doc/first-app/UserManual"',
                '"/usr/share/doc/first-app/license"',
                '"/usr/share/man/man1/first-app.1.gz"',
                "",
                "%changelog",
                "First App Changelog",
            ]
        )

    # A source tarball was created with the right content
    archive_file = bundle_path / "rpmbuild/SOURCES/first-app-0.0.1.tar.gz"
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

    # rpmbuild was invoked
    package_command.tools.app_tools[
        first_app_rpm
    ].app_context.run.assert_called_once_with(
        [
            "rpmbuild",
            "-bb",
            "--define",
            f"_topdir {bundle_path / 'rpmbuild'}",
            "./rpmbuild/SPECS/first-app.spec",
        ],
        check=True,
        cwd=bundle_path,
    )

    # The rpm was moved into the final location
    package_command.tools.shutil.move.assert_called_once_with(
        bundle_path
        / "rpmbuild"
        / "RPMS"
        / "wonky"
        / "first-app-0.0.1-1.fcXX.wonky.rpm",
        tmp_path / "base_path/dist/first-app-0.0.1-1.fcXX.wonky.rpm",
    )


@pytest.mark.skipif(sys.platform == "win32", reason="Can't build RPMs on Windows")
def test_rpm_re_package(package_command, first_app_rpm, tmp_path):
    """A rpm app that has previously been packaged can be re-packaged."""
    bundle_path = tmp_path / "base_path/build/first-app/somevendor/surprising"

    # Create an old spec file and tarball that will be overwritten.
    create_file(
        bundle_path / "rpmbuild/SPECS/first-app.spec",
        "Old spec content",
    )
    create_tgz_file(
        bundle_path / "rpmbuild/SOURCES/first-app-0.0.1.tar.gz",
        [("old.txt", "old content")],
    )

    # Package the app
    package_command.package_app(first_app_rpm)

    # rpmbuild layout has been generated
    assert (bundle_path / "rpmbuild/BUILD").exists()
    assert (bundle_path / "rpmbuild/BUILDROOT").exists()
    assert (bundle_path / "rpmbuild/RPMS").exists()
    assert (bundle_path / "rpmbuild/SOURCES").exists()
    assert (bundle_path / "rpmbuild/SRPMS").exists()
    assert (bundle_path / "rpmbuild/SPECS").exists()

    # The spec file is written
    assert (bundle_path / "rpmbuild/SPECS/first-app.spec").exists()
    with (bundle_path / "rpmbuild/SPECS/first-app.spec").open(encoding="utf-8") as f:
        assert f.read() == "\n".join(
            [
                "%global __brp_mangle_shebangs %{nil}",
                "%global __brp_strip %{nil}",
                "%global __brp_strip_static_archive %{nil}",
                "%global __brp_strip_comment_note %{nil}",
                "%global __brp_check_rpaths %{nil}",
                "%global __requires_exclude_from ^%{_libdir}/first-app/.*$",
                "%global __provides_exclude_from ^%{_libdir}/first-app/.*$",
                "%global _enable_debug_package 0",
                "%global debug_package %{nil}",
                "",
                "Name:           first-app",
                "Version:        0.0.1",
                "Release:        1%{?dist}",
                "Summary:        The first simple app \\ demonstration",
                "",
                "License:        Unknown",
                "URL:            https://example.com/first-app",
                "Source0:        %{name}-%{version}.tar.gz",
                "",
                "Requires:       python3",
                "",
                "ExclusiveArch:  wonky",
                "",
                "%description",
                "Long description",
                "for the app",
                "",
                "%prep",
                "%autosetup",
                "",
                "%build",
                "",
                "%install",
                "cp -r usr %{buildroot}/usr",
                "",
                "%files",
                '"/usr/bin/first-app"',
                '%dir "/usr/lib/first-app"',
                '%dir "/usr/lib/first-app/app"',
                '"/usr/lib/first-app/app/support.so"',
                '"/usr/lib/first-app/app/support_same_perms.so"',
                '%dir "/usr/lib/first-app/app_packages"',
                '%dir "/usr/lib/first-app/app_packages/firstlib"',
                '"/usr/lib/first-app/app_packages/firstlib/first.so"',
                '"/usr/lib/first-app/app_packages/firstlib/first.so.1.0"',
                '%dir "/usr/lib/first-app/app_packages/secondlib"',
                '"/usr/lib/first-app/app_packages/secondlib/second_a.so"',
                '"/usr/lib/first-app/app_packages/secondlib/second_b.so"',
                '%dir "/usr/share/doc/first-app"',
                '"/usr/share/doc/first-app/UserManual"',
                '"/usr/share/doc/first-app/license"',
                '"/usr/share/man/man1/first-app.1.gz"',
                "",
                "%changelog",
                "First App Changelog",
            ]
        )

    # A source tarball was created with the right content
    archive_file = bundle_path / "rpmbuild/SOURCES/first-app-0.0.1.tar.gz"
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

    # rpmbuild was invoked
    package_command.tools.app_tools[
        first_app_rpm
    ].app_context.run.assert_called_once_with(
        [
            "rpmbuild",
            "-bb",
            "--define",
            f"_topdir {bundle_path / 'rpmbuild'}",
            "./rpmbuild/SPECS/first-app.spec",
        ],
        check=True,
        cwd=bundle_path,
    )

    # The rpm was moved into the final location
    package_command.tools.shutil.move.assert_called_once_with(
        bundle_path
        / "rpmbuild"
        / "RPMS"
        / "wonky"
        / "first-app-0.0.1-1.fcXX.wonky.rpm",
        tmp_path / "base_path/dist/first-app-0.0.1-1.fcXX.wonky.rpm",
    )


@pytest.mark.skipif(sys.platform == "win32", reason="Can't build RPMs on Windows")
def test_rpm_package_no_long_description(package_command, first_app_rpm, tmp_path):
    """A rpm app without a long description raises an error."""
    bundle_path = tmp_path / "base_path/build/first-app/somevendor/surprising"

    # Delete the long description
    first_app_rpm.long_description = None

    # Packaging the app will fail
    with pytest.raises(
        BriefcaseCommandError,
        match=r"App configuration does not define `long_description`. Red Hat projects require a long description.",
    ):
        package_command.package_app(first_app_rpm)

    # The spec file and tarball won't be written
    assert not (bundle_path / "rpmbuild/SPECS/first-app.spec").exists()
    assert not (bundle_path / "rpmbuild/SOURCES/first-app-0.0.1.tar.gz").exists()


@pytest.mark.skipif(sys.platform == "win32", reason="Can't build RPMs on Windows")
def test_rpm_package_extra_requirements(package_command, first_app_rpm, tmp_path):
    """A rpm app can be packaged with extra runtime requirements and config features."""
    bundle_path = tmp_path / "base_path/build/first-app/somevendor/surprising"

    # Add system requirements and other optional settings.
    first_app_rpm.system_runtime_requires = ["first", "second"]
    first_app_rpm.revision = 42
    first_app_rpm.license = "BSD License"

    # Package the app
    package_command.package_app(first_app_rpm)

    # rpmbuild layout has been generated
    assert (bundle_path / "rpmbuild/BUILD").exists()
    assert (bundle_path / "rpmbuild/BUILDROOT").exists()
    assert (bundle_path / "rpmbuild/RPMS").exists()
    assert (bundle_path / "rpmbuild/SOURCES").exists()
    assert (bundle_path / "rpmbuild/SRPMS").exists()
    assert (bundle_path / "rpmbuild/SPECS").exists()

    # The spec file is written
    assert (bundle_path / "rpmbuild/SPECS/first-app.spec").exists()
    with (bundle_path / "rpmbuild/SPECS/first-app.spec").open(encoding="utf-8") as f:
        assert f.read() == "\n".join(
            [
                "%global __brp_mangle_shebangs %{nil}",
                "%global __brp_strip %{nil}",
                "%global __brp_strip_static_archive %{nil}",
                "%global __brp_strip_comment_note %{nil}",
                "%global __brp_check_rpaths %{nil}",
                "%global __requires_exclude_from ^%{_libdir}/first-app/.*$",
                "%global __provides_exclude_from ^%{_libdir}/first-app/.*$",
                "%global _enable_debug_package 0",
                "%global debug_package %{nil}",
                "",
                "Name:           first-app",
                "Version:        0.0.1",
                "Release:        42%{?dist}",
                "Summary:        The first simple app \\ demonstration",
                "",
                "License:        BSD License",
                "URL:            https://example.com/first-app",
                "Source0:        %{name}-%{version}.tar.gz",
                "",
                "Requires:       python3",
                "Requires:       first",
                "Requires:       second",
                "",
                "ExclusiveArch:  wonky",
                "",
                "%description",
                "Long description",
                "for the app",
                "",
                "%prep",
                "%autosetup",
                "",
                "%build",
                "",
                "%install",
                "cp -r usr %{buildroot}/usr",
                "",
                "%files",
                '"/usr/bin/first-app"',
                '%dir "/usr/lib/first-app"',
                '%dir "/usr/lib/first-app/app"',
                '"/usr/lib/first-app/app/support.so"',
                '"/usr/lib/first-app/app/support_same_perms.so"',
                '%dir "/usr/lib/first-app/app_packages"',
                '%dir "/usr/lib/first-app/app_packages/firstlib"',
                '"/usr/lib/first-app/app_packages/firstlib/first.so"',
                '"/usr/lib/first-app/app_packages/firstlib/first.so.1.0"',
                '%dir "/usr/lib/first-app/app_packages/secondlib"',
                '"/usr/lib/first-app/app_packages/secondlib/second_a.so"',
                '"/usr/lib/first-app/app_packages/secondlib/second_b.so"',
                '%dir "/usr/share/doc/first-app"',
                '"/usr/share/doc/first-app/UserManual"',
                '"/usr/share/doc/first-app/license"',
                '"/usr/share/man/man1/first-app.1.gz"',
                "",
                "%changelog",
                "First App Changelog",
            ]
        )

    # A source tarball was created
    archive_file = bundle_path / "rpmbuild/SOURCES/first-app-0.0.1.tar.gz"
    assert archive_file.exists()

    # rpmbuild was invoked
    package_command.tools.app_tools[
        first_app_rpm
    ].app_context.run.assert_called_once_with(
        [
            "rpmbuild",
            "-bb",
            "--define",
            f"_topdir {bundle_path / 'rpmbuild'}",
            "./rpmbuild/SPECS/first-app.spec",
        ],
        check=True,
        cwd=bundle_path,
    )

    # The rpm was moved into the final location
    package_command.tools.shutil.move.assert_called_once_with(
        bundle_path
        / "rpmbuild"
        / "RPMS"
        / "wonky"
        / "first-app-0.0.1-42.fcXX.wonky.rpm",
        tmp_path / "base_path/dist/first-app-0.0.1-42.fcXX.wonky.rpm",
    )


@pytest.mark.skipif(sys.platform == "win32", reason="Can't build RPMs on Windows")
def test_rpm_package_failure(package_command, first_app_rpm, tmp_path):
    """If an packaging doesn't succeed, an error is raised."""
    bundle_path = tmp_path / "base_path/build/first-app/somevendor/surprising"

    # Mock a packaging failure
    package_command.tools.app_tools[first_app_rpm].app_context.run.side_effect = (
        subprocess.CalledProcessError(cmd="rpmbuild ...", returncode=-1)
    )

    # Package the app; this will fail
    with pytest.raises(
        BriefcaseCommandError, match=r"Error while building .rpm package for first-app."
    ):
        package_command.package_app(first_app_rpm)

    # rpmbuild layout has been generated
    assert (bundle_path / "rpmbuild/BUILD").exists()
    assert (bundle_path / "rpmbuild/BUILDROOT").exists()
    assert (bundle_path / "rpmbuild/RPMS").exists()
    assert (bundle_path / "rpmbuild/SOURCES").exists()
    assert (bundle_path / "rpmbuild/SRPMS").exists()
    assert (bundle_path / "rpmbuild/SPECS").exists()

    # The spec file is written
    assert (bundle_path / "rpmbuild/SPECS/first-app.spec").exists()

    # A source tarball was created
    archive_file = bundle_path / "rpmbuild/SOURCES/first-app-0.0.1.tar.gz"
    assert archive_file.exists()

    # rpmbuild was invoked
    package_command.tools.app_tools[
        first_app_rpm
    ].app_context.run.assert_called_once_with(
        [
            "rpmbuild",
            "-bb",
            "--define",
            f"_topdir {bundle_path / 'rpmbuild'}",
            "./rpmbuild/SPECS/first-app.spec",
        ],
        check=True,
        cwd=bundle_path,
    )

    # The deb wasn't built, so it wasn't moved.
    package_command.tools.shutil.move.assert_not_called()


@pytest.mark.skipif(sys.platform == "win32", reason="Can't build RPMs on Windows")
def test_no_changelog(package_command, first_app_rpm, tmp_path):
    """If an packaging doesn't succeed, an error is raised."""
    bundle_path = tmp_path / "base_path/build/first-app/somevendor/surprising"

    # Remove the changelog file
    (tmp_path / "base_path/CHANGELOG").unlink()

    # Package the app; this will fail
    with pytest.raises(
        BriefcaseCommandError, match=r"Your project does not contain a CHANGELOG file."
    ):
        package_command.package_app(first_app_rpm)

    # rpmbuild layout has been generated
    assert (bundle_path / "rpmbuild/BUILD").exists()
    assert (bundle_path / "rpmbuild/BUILDROOT").exists()
    assert (bundle_path / "rpmbuild/RPMS").exists()
    assert (bundle_path / "rpmbuild/SOURCES").exists()
    assert (bundle_path / "rpmbuild/SRPMS").exists()
    assert (bundle_path / "rpmbuild/SPECS").exists()

    # The spec file will exist (however, it will be incomplete)
    assert (bundle_path / "rpmbuild/SPECS/first-app.spec").exists()

    # No source tarball was created
    archive_file = bundle_path / "rpmbuild/SOURCES/first-app-0.0.1.tar.gz"
    assert not archive_file.exists()

    # rpmbuild wasn't invoked
    package_command.tools.app_tools[first_app_rpm].app_context.run.assert_not_called()

    # The deb wasn't built, so it wasn't moved.
    package_command.tools.shutil.move.assert_not_called()
