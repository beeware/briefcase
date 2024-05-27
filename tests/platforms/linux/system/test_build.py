import gzip
import os
import subprocess
import sys
from unittest import mock

import pytest

from briefcase.console import Console, Log
from briefcase.exceptions import BriefcaseCommandError
from briefcase.platforms.linux.system import LinuxSystemBuildCommand

from ....utils import create_file


@pytest.fixture
def build_command(tmp_path, first_app):
    command = LinuxSystemBuildCommand(
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
    bundle_path = tmp_path / "base_path/build/first-app/somevendor/surprising"
    build_command.tools[first_app].app_context.run.assert_called_with(
        ["make", "-C", "bootstrap", "install"],
        check=True,
        cwd=bundle_path,
    )

    # The license file has been installed
    doc_path = bundle_path / "first-app-0.0.1/usr/share/doc/first-app"
    assert (doc_path / "copyright").exists()
    with (doc_path / "copyright").open(encoding="utf-8") as f:
        assert f.read() == "First App License"

    # The Changelog has been compressed and installed
    assert (doc_path / "changelog.gz").exists()
    with gzip.open(doc_path / "changelog.gz") as f:
        assert f.read().decode() == "First App Changelog"

    # The manpage has been installed
    man_path = bundle_path / "first-app-0.0.1/usr/share/man/man1"
    assert (man_path / "first-app.1.gz").exists()
    with gzip.open(man_path / "first-app.1.gz") as f:
        assert f.read().decode() == "First App manpage"

    # Problematic permissions have been updated
    lib_dir = bundle_path / "first-app-0.0.1/usr/lib/first-app"
    # 775 -> 775
    assert os.stat(lib_dir / "app/support.so").st_mode & 0o777 == 0o755
    # 664 -> 644
    assert (
        os.stat(lib_dir / "app_packages/secondlib/second_a.so").st_mode & 0o777 == 0o644
    )
    # no perms change
    assert os.stat(lib_dir / "app/support_same_perms.so").st_mode & 0o777 == 0o744

    # Strip has been invoked on the binary
    build_command.tools.subprocess.check_output.assert_called_once_with(
        [
            "strip",
            bundle_path / "first-app-0.0.1/usr/bin/first-app",
        ]
    )


def test_build_bootstrap_failed(build_command, first_app, tmp_path):
    """If the bootstrap binary can't be compiled, an error is raised."""
    # Mock a build failure
    build_command.tools[first_app].app_context.run.side_effect = (
        subprocess.CalledProcessError(cmd=["make ..."], returncode=-1)
    )

    # Build the app; it will fail
    with pytest.raises(
        BriefcaseCommandError,
        match=r"Error building bootstrap binary for first-app.",
    ):
        build_command.build_app(first_app)

    # An attempt to do the compile occurred.
    bundle_path = tmp_path / "base_path/build/first-app/somevendor/surprising"
    build_command.tools[first_app].app_context.run.assert_called_with(
        ["make", "-C", "bootstrap", "install"],
        check=True,
        cwd=bundle_path,
    )


def test_missing_license(build_command, first_app, tmp_path):
    """If the license source file is missing, an error is raised."""
    bundle_path = tmp_path / "base_path/build/first-app/somevendor/surprising"

    # Delete the license source
    (tmp_path / "base_path/LICENSE").unlink()

    # Build the app; it will fail
    with pytest.raises(
        BriefcaseCommandError,
        match=r"Your `pyproject.toml` specifies a license file of 'LICENSE'",
    ):
        build_command.build_app(first_app)

    # The bootstrap binary was compiled
    build_command.tools[first_app].app_context.run.assert_called_with(
        ["make", "-C", "bootstrap", "install"],
        check=True,
        cwd=bundle_path,
    )


def test_specified_license_file_is_copied(build_command, first_app, tmp_path):
    """The specified license file is copied if a license file is specified."""
    create_file(tmp_path / "base_path/LICENSE.txt", "The Actual First App License")
    first_app.license["file"] = "LICENSE.txt"

    # Build the app
    build_command.build_app(first_app)

    # The correct license file has been copied
    doc_folder = (
        build_command.bundle_path(first_app)
        / f"{first_app.app_name}-{first_app.version}"
        / "usr"
        / "share"
        / "doc"
        / first_app.app_name
    )
    assert (doc_folder / "copyright").read_text(
        encoding="utf-8"
    ) == "The Actual First App License"


def test_license_text_is_saved(build_command, first_app):
    """The license text is saved as a file in the bundle."""
    first_app.license = {"text": "Some license text"}

    # Build the app
    build_command.build_app(first_app)

    # The license text has been saved
    doc_folder = (
        build_command.bundle_path(first_app)
        / f"{first_app.app_name}-{first_app.version}"
        / "usr"
        / "share"
        / "doc"
        / first_app.app_name
    )

    assert (doc_folder / "copyright").read_text(encoding="utf-8") == "Some license text"


def test_license_text_warns_with_single_line_license(build_command, first_app):
    """A warning is logged if the license text is a single line."""

    first_app.license = {"text": "Some license text"}
    build_command.logger.warning = mock.MagicMock()

    # Build the app
    build_command.build_app(first_app)

    build_command.logger.warning.assert_called_once_with(
        """
Your app specifies a license using `license.text`, but the value doesn't appear to be a
full license. Briefcase will generate a `copyright` file for your project; you should
ensure that the contents of this file is adequate.
"""
    )


def test_exception_with_no_license(build_command, first_app):
    """An exception is raised if there is no license defined."""

    first_app.license = {}
    build_command.logger.warning = mock.MagicMock()

    # Build the app
    with pytest.raises(
        BriefcaseCommandError,
        match="Your project does not contain a LICENSE definition.",
    ):
        build_command.build_app(first_app)


def test_license_text_doesnt_warn_with_multi_line_license(
    build_command, first_app, tmp_path
):
    """No warning is logged if the license text is multi-line."""
    first_app.license = {"text": "Some license text\nsome more text"}
    build_command.logger.warning = mock.MagicMock()

    # Build the app
    build_command.build_app(first_app)
    build_command.logger.warning.assert_not_called()


def test_missing_changelog(build_command, first_app, tmp_path):
    """If the changelog source file is missing, an error is raised."""
    bundle_path = tmp_path / "base_path/build/first-app/somevendor/surprising"

    # Delete the changelog source
    (tmp_path / "base_path/CHANGELOG").unlink()

    # Build the app; it will fail
    with pytest.raises(
        BriefcaseCommandError,
        match=r"Your project does not contain a CHANGELOG file.",
    ):
        build_command.build_app(first_app)

    # The bootstrap binary was compiled
    build_command.tools[first_app].app_context.run.assert_called_with(
        ["make", "-C", "bootstrap", "install"],
        check=True,
        cwd=bundle_path,
    )

    # The license file has been installed
    doc_path = bundle_path / "first-app-0.0.1/usr/share/doc/first-app"
    assert (doc_path / "copyright").exists()
    with (doc_path / "copyright").open(encoding="utf-8") as f:
        assert f.read() == "First App License"


def test_missing_manpage(build_command, first_app, tmp_path):
    """If the manpage source file is missing, an error is raised."""
    bundle_path = tmp_path / "base_path/build/first-app/somevendor/surprising"

    # Delete the manpage source
    (bundle_path / "first-app.1").unlink()

    # Build the app; it will fail
    with pytest.raises(
        BriefcaseCommandError,
        match=r"Template does not provide a manpage source file `first-app\.1`",
    ):
        build_command.build_app(first_app)

    # The bootstrap binary was compiled
    build_command.tools[first_app].app_context.run.assert_called_with(
        ["make", "-C", "bootstrap", "install"],
        check=True,
        cwd=bundle_path,
    )

    # The license file has been installed
    doc_path = bundle_path / "first-app-0.0.1/usr/share/doc/first-app"
    assert (doc_path / "copyright").exists()
    with (doc_path / "copyright").open(encoding="utf-8") as f:
        assert f.read() == "First App License"

    # The Changelog has been compressed and installed
    assert (doc_path / "changelog.gz").exists()
    with gzip.open(doc_path / "changelog.gz") as f:
        assert f.read().decode() == "First App Changelog"
