import shlex
import subprocess
from pathlib import Path
from unittest import mock

import pytest

from briefcase.exceptions import BriefcaseCommandError
from briefcase.integrations.docker import DockerAppContext

from .conftest import JANE


def make_docker_context(package_command, first_app):
    """Replace the app context with a Docker context with a mocked run method."""
    app_context = DockerAppContext(tools=package_command.tools, app=first_app)
    app_context.run = mock.MagicMock()
    package_command.tools[first_app].app_context = app_context
    return app_context


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


@pytest.mark.parametrize(
    ("format", "sign_command"),
    [
        (
            "deb",
            [
                "debsigs",
                "--sign=origin",
                f"--default-key={JANE}",
                "/path/to/dist/first-app.deb",
            ],
        ),
        (
            "rpm",
            [
                "rpmsign",
                "--define",
                f"_gpg_name {JANE}",
                "--addsign",
                "/path/to/dist/first-app.rpm",
            ],
        ),
        (
            "pkg",
            [
                "gpg",
                "--detach-sign",
                "-u",
                JANE,
                "--output",
                "/path/to/dist/first-app.pkg.tar.zst.sig",
                "/path/to/dist/first-app.pkg.tar.zst",
            ],
        ),
    ],
)
def test_sign_package_in_docker(
    package_command,
    first_app,
    mock_gpg,
    format,
    sign_command,
):
    """A package is signed inside a Docker container after importing the signing key."""
    first_app.packaging_format = format
    dist_path = Path("/path/to/dist/first-app.pkg.tar.zst")
    if format == "deb":
        dist_path = Path("/path/to/dist/first-app.deb")
    elif format == "rpm":
        dist_path = Path("/path/to/dist/first-app.rpm")
    package_command.distribution_path = mock.MagicMock(return_value=dist_path)
    if format == "pkg":
        package_command.signature_path = mock.MagicMock(
            return_value=Path("/path/to/dist/first-app.pkg.tar.zst.sig")
        )
    make_docker_context(package_command, first_app)

    key_file_path = package_command.data_path / f"{first_app.app_name}-signing-key.gpg"
    key_file_path.touch()

    package_command.sign_package(first_app, identity=JANE)

    mock_gpg.export_secret_key.assert_called_once_with(JANE, key_file_path)
    package_command.tools.os.chmod.assert_called_once_with(key_file_path, 0o600)

    import_command = ["gpg", "--batch", "--import", str(key_file_path)]
    command = " && ".join(
        " ".join(shlex.quote(arg) for arg in cmd)
        for cmd in [import_command, sign_command]
    )
    package_command.tools[first_app].app_context.run.assert_called_once_with(
        ["sh", "-c", command],
        check=True,
        mounts=[(package_command.dist_path, "/dist")],
    )

    # The exported key file is removed after signing.
    assert not key_file_path.exists()


def test_sign_package_error_in_docker(package_command, first_app, mock_gpg):
    """If signing inside Docker fails, an error is raised and the key file is
    removed."""
    first_app.packaging_format = "deb"
    package_command.distribution_path = mock.MagicMock(
        return_value=Path("/path/to/dist/first-app.deb")
    )
    app_context = make_docker_context(package_command, first_app)
    app_context.run.side_effect = subprocess.CalledProcessError(
        returncode=1,
        cmd=["sh", "-c", "gpg --batch --import /path/to/key && debsigs"],
    )

    key_file_path = package_command.data_path / f"{first_app.app_name}-signing-key.gpg"
    key_file_path.touch()

    with pytest.raises(
        BriefcaseCommandError,
        match=r"Error while signing .deb package for first-app.",
    ):
        package_command.sign_package(first_app, identity=JANE)

    # The exported key file is removed after signing.
    assert not key_file_path.exists()


def test_sign_package_key_export_error_in_docker(package_command, first_app, mock_gpg):
    """If the signing key can't be exported, an error is raised and the key file is
    removed."""
    first_app.packaging_format = "deb"
    package_command.distribution_path = mock.MagicMock(
        return_value=Path("/path/to/dist/first-app.deb")
    )
    make_docker_context(package_command, first_app)
    mock_gpg.export_secret_key.side_effect = BriefcaseCommandError("boom")

    key_file_path = package_command.data_path / f"{first_app.app_name}-signing-key.gpg"
    key_file_path.touch()

    with pytest.raises(BriefcaseCommandError, match=r"boom"):
        package_command.sign_package(first_app, identity=JANE)

    package_command.tools[first_app].app_context.run.assert_not_called()
    assert not key_file_path.exists()
