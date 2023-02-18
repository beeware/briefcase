import gzip
import os
import subprocess
import sys
from unittest import mock

import pytest

from briefcase.console import Console, Log
from briefcase.exceptions import BriefcaseCommandError
from briefcase.platforms.linux.deb import LinuxDebBuildCommand


@pytest.fixture
def build_command(tmp_path, first_app):
    command = LinuxDebBuildCommand(
        logger=Log(),
        console=Console(),
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
        apps={"first": first_app},
    )
    command.tools.host_os = "Linux"
    command.tools.host_arch = "wonky"

    # Mock subprocess
    command.tools.subprocess = mock.MagicMock()

    # Mock the app context
    command.tools.app_tools[first_app].app_context = mock.MagicMock()

    return command


@pytest.mark.skipif(sys.platform == "win32", reason="Can't build Linux apps on Windows")
def test_build_app(build_command, first_app, tmp_path):
    """An app can be built as a deb."""
    # Build the app
    build_command.build_app(first_app)

    # The bootstrap binary was compiled
    bundle_path = (
        tmp_path
        / "base_path"
        / "linux"
        / "somevendor"
        / "surprising"
        / "system"
        / "First App"
    )
    build_command.tools[first_app].app_context.run.assert_called_with(
        ["make", "-C", "bootstrap", "install"],
        check=True,
        cwd=bundle_path,
    )

    # The license file has been installed
    doc_path = (
        bundle_path / "first-app_0.0.1-1_wonky" / "usr" / "share" / "doc" / "first-app"
    )
    assert (doc_path / "copyright").exists()
    with (doc_path / "copyright").open() as f:
        assert f.read() == "First App License"

    # The Changelog has been compressed and installed
    assert (doc_path / "changelog.gz").exists()
    with gzip.open(doc_path / "changelog.gz") as f:
        assert f.read().decode() == "First App Changelog"

    # The manpage has been installed
    man_path = (
        bundle_path / "first-app_0.0.1-1_wonky" / "usr" / "share" / "man" / "man1"
    )
    assert (man_path / "first-app.1.gz").exists()
    with gzip.open(man_path / "first-app.1.gz") as f:
        assert f.read().decode() == "First App manpage"

    # Problematic permissions have been updated
    lib_dir = bundle_path / "first-app_0.0.1-1_wonky" / "usr" / "lib" / "first-app"
    # 775 -> 775
    assert os.stat(lib_dir / "app" / "support.so").st_mode & 0o777 == 0o755
    # 664 -> 644
    assert (
        os.stat(lib_dir / "app_packages" / "secondlib" / "second_a.so").st_mode & 0o777
        == 0o644
    )

    # Strip has been invoked on all binaries
    assert build_command.tools.subprocess.check_output.mock_calls == [
        mock.call(["strip", lib_dir / "app" / "support.so"]),
        mock.call(["strip", lib_dir / "app_packages" / "firstlib" / "first.so"]),
        mock.call(["strip", lib_dir / "app_packages" / "secondlib" / "second_a.so"]),
        mock.call(["strip", lib_dir / "app_packages" / "secondlib" / "second_b.so"]),
        mock.call(["strip", lib_dir / "app_packages" / "firstlib" / "first.so.1.0"]),
        mock.call(
            [
                "strip",
                bundle_path / "first-app_0.0.1-1_wonky" / "usr" / "bin" / "first-app",
            ]
        ),
    ]


def test_build_bootstrap_failed(build_command, first_app, tmp_path):
    """If the bootstrap binary can't be compiled, an error is raised."""
    # Mock a build failure
    build_command.tools[
        first_app
    ].app_context.run.side_effect = subprocess.CalledProcessError(
        cmd=["make ..."], returncode=-1
    )

    # Build the app; it will fail
    with pytest.raises(
        BriefcaseCommandError, match=r"Error building bootstrap binary for first-app."
    ):
        build_command.build_app(first_app)

    # An attempt to do the compile occurred.
    bundle_path = (
        tmp_path
        / "base_path"
        / "linux"
        / "somevendor"
        / "surprising"
        / "system"
        / "First App"
    )
    build_command.tools[first_app].app_context.run.assert_called_with(
        ["make", "-C", "bootstrap", "install"],
        check=True,
        cwd=bundle_path,
    )


def test_missing_license(build_command, first_app, tmp_path):
    """If the license source file is missing, an error is raised."""
    bundle_path = (
        tmp_path
        / "base_path"
        / "linux"
        / "somevendor"
        / "surprising"
        / "system"
        / "First App"
    )

    # Delete the license source
    (bundle_path / "LICENSE").unlink()

    # Build the app; it will fail
    with pytest.raises(
        BriefcaseCommandError,
        match=r"LICENSE source file is missing",
    ):
        build_command.build_app(first_app)

    # The bootstrap binary was compiled
    build_command.tools[first_app].app_context.run.assert_called_with(
        ["make", "-C", "bootstrap", "install"],
        check=True,
        cwd=bundle_path,
    )


def test_missing_changelog(build_command, first_app, tmp_path):
    """If the changelog source file is missing, an error is raised."""
    bundle_path = (
        tmp_path
        / "base_path"
        / "linux"
        / "somevendor"
        / "surprising"
        / "system"
        / "First App"
    )

    # Delete the changelog source
    (bundle_path / "CHANGELOG").unlink()

    # Build the app; it will fail
    with pytest.raises(
        BriefcaseCommandError,
        match=r"CHANGELOG source file is missing",
    ):
        build_command.build_app(first_app)

    # The bootstrap binary was compiled
    build_command.tools[first_app].app_context.run.assert_called_with(
        ["make", "-C", "bootstrap", "install"],
        check=True,
        cwd=bundle_path,
    )

    # The license file has been installed
    doc_path = (
        bundle_path / "first-app_0.0.1-1_wonky" / "usr" / "share" / "doc" / "first-app"
    )
    assert (doc_path / "copyright").exists()
    with (doc_path / "copyright").open() as f:
        assert f.read() == "First App License"


def test_missing_manpage(build_command, first_app, tmp_path):
    """If the manpage source file is missing, an error is raised."""
    bundle_path = (
        tmp_path
        / "base_path"
        / "linux"
        / "somevendor"
        / "surprising"
        / "system"
        / "First App"
    )

    # Delete the manpage source
    (bundle_path / "first-app.1").unlink()

    # Build the app; it will fail
    with pytest.raises(
        BriefcaseCommandError,
        match=r"manpage source file `first-app\.1` is missing",
    ):
        build_command.build_app(first_app)

    # The bootstrap binary was compiled
    build_command.tools[first_app].app_context.run.assert_called_with(
        ["make", "-C", "bootstrap", "install"],
        check=True,
        cwd=bundle_path,
    )

    # The license file has been installed
    doc_path = (
        bundle_path / "first-app_0.0.1-1_wonky" / "usr" / "share" / "doc" / "first-app"
    )
    assert (doc_path / "copyright").exists()
    with (doc_path / "copyright").open() as f:
        assert f.read() == "First App License"

    # The Changelog has been compressed and installed
    assert (doc_path / "changelog.gz").exists()
    with gzip.open(doc_path / "changelog.gz") as f:
        assert f.read().decode() == "First App Changelog"
