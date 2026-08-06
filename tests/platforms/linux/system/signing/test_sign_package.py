import subprocess
from pathlib import Path
from unittest import mock

import pytest

from briefcase.exceptions import BriefcaseCommandError

from .conftest import JANE


def test_sign_deb_package(package_command, first_app):
    """A .deb package is signed with debsigs."""
    first_app.packaging_format = "deb"
    dist_path = Path("/path/to/dist/first-app.deb")
    package_command.distribution_path = mock.MagicMock(return_value=dist_path)

    package_command.sign_package(first_app, identity=JANE)

    package_command.tools[first_app].app_context.run.assert_called_once_with(
        ["debsigs", "--sign=origin", f"--default-key={JANE}", str(dist_path)],
        check=True,
    )


def test_sign_rpm_package(package_command, first_app):
    """A .rpm package is signed with rpmsign."""
    first_app.packaging_format = "rpm"
    dist_path = Path("/path/to/dist/first-app.rpm")
    package_command.distribution_path = mock.MagicMock(return_value=dist_path)

    package_command.sign_package(first_app, identity=JANE)

    package_command.tools[first_app].app_context.run.assert_called_once_with(
        [
            "rpmsign",
            "--define",
            f"_gpg_name {JANE}",
            "--addsign",
            str(dist_path),
        ],
        check=True,
    )


def test_sign_pkg_package(package_command, first_app):
    """A .pkg.tar.zst package is signed with a detached gpg signature."""
    first_app.packaging_format = "pkg"
    dist_path = Path("/path/to/dist/first-app.pkg.tar.zst")
    package_command.distribution_path = mock.MagicMock(return_value=dist_path)
    package_command.signature_path = mock.MagicMock(
        return_value=Path("/path/to/dist/first-app.pkg.tar.zst.sig")
    )

    package_command.sign_package(first_app, identity=JANE)

    package_command.tools[first_app].app_context.run.assert_called_once_with(
        [
            "gpg",
            "--detach-sign",
            "-u",
            JANE,
            "--output",
            str(Path("/path/to/dist/first-app.pkg.tar.zst.sig")),
            str(dist_path),
        ],
        check=True,
    )


def test_sign_package_error(package_command, first_app):
    """If signing fails, an error is raised."""
    first_app.packaging_format = "deb"
    package_command.tools[
        first_app
    ].app_context.run.side_effect = subprocess.CalledProcessError(
        returncode=1,
        cmd=["debsigs", "--sign=origin", "--default-key=DEADBEEF"],
    )
    package_command.distribution_path = mock.MagicMock(
        return_value=Path("/path/to/dist/first-app.deb")
    )

    with pytest.raises(
        BriefcaseCommandError,
        match=r"Error while signing .deb package for first-app.",
    ):
        package_command.sign_package(first_app, identity=JANE)
