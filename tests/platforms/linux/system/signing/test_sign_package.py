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
    # Enable Docker for the command.
    package_command.target_image = "somevendor:surprising"
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
    ("format", "extension"),
    [
        ("deb", "deb"),
        ("rpm", "rpm"),
        ("pkg", "pkg.tar.zst"),
    ],
)
def test_sign_package_in_docker(
    package_command,
    first_app,
    mock_gpg,
    format,
    extension,
):
    """A package is signed inside a Docker container after importing the signing key.

    The sign command uses host paths; the Docker layer is responsible for rewriting them
    to their container equivalents.
    """
    first_app.packaging_format = format
    dist_path = Path("/path/to/dist") / f"first-app.{extension}"
    package_command.distribution_path = mock.MagicMock(return_value=dist_path)
    if format == "deb":
        sign_command = [
            "debsigs",
            "--sign=origin",
            f"--default-key={JANE}",
            str(dist_path),
        ]
    elif format == "rpm":
        sign_command = [
            "rpmsign",
            "--define",
            f"_gpg_name {JANE}",
            "--addsign",
            str(dist_path),
        ]
    else:
        signature_path = Path(f"{dist_path}.sig")
        package_command.signature_path = mock.MagicMock(return_value=signature_path)
        sign_command = [
            "gpg",
            "--detach-sign",
            "-u",
            JANE,
            "--output",
            str(signature_path),
            str(dist_path),
        ]

    make_docker_context(package_command, first_app)

    public_key_path = package_command.bundle_path(first_app) / "signing-public-key.gpg"
    public_key_path.touch()
    agent_socket_path = Path("/run/user/1000/gnupg/S.gpg-agent")
    mock_gpg.agent_socket_path.return_value = agent_socket_path

    package_command.sign_package(first_app, identity=JANE)

    mock_gpg.export_public_key.assert_called_once_with(JANE, public_key_path)
    package_command.tools.os.chmod.assert_called_once_with(public_key_path, 0o644)

    gnupg_home = "/tmp/briefcase-gnupg"
    container_commands = [
        ["rm", "-rf", gnupg_home],
        ["mkdir", "-p", gnupg_home],
        ["chmod", "700", gnupg_home],
        ["gpg", "--batch", "--import", str(public_key_path)],
        [
            "ln",
            "-sf",
            "/run/briefcase/gnupg-agent/S.gpg-agent",
            f"{gnupg_home}/S.gpg-agent",
        ],
        sign_command,
    ]
    command = " && ".join(
        " ".join(shlex.quote(arg) for arg in cmd)
        for cmd in container_commands
    )
    package_command.tools[first_app].app_context.run.assert_called_once_with(
        ["sh", "-c", command],
        check=True,
        mounts=[
            (agent_socket_path.parent, "/run/briefcase/gnupg-agent"),
            (package_command.dist_path, "/dist"),
        ],
        env={"GNUPGHOME": gnupg_home},
    )

    # The exported public key is removed after signing.
    assert not public_key_path.exists()


def test_sign_package_error_in_docker(package_command, first_app, mock_gpg):
    """If signing inside Docker fails, an error is raised and the key file is
    removed."""
    first_app.packaging_format = "deb"
    package_command.distribution_path = mock.MagicMock(
        return_value=Path("/path/to/dist/first-app.deb")
    )
    app_context = make_docker_context(package_command, first_app)
    mock_gpg.agent_socket_path.return_value = Path(
        "/run/user/1000/gnupg/S.gpg-agent"
    )
    app_context.run.side_effect = subprocess.CalledProcessError(
        returncode=1,
        cmd=["sh", "-c", "debsigs"],
    )

    public_key_path = package_command.bundle_path(first_app) / "signing-public-key.gpg"
    public_key_path.touch()

    with pytest.raises(
        BriefcaseCommandError,
        match=r"Error while signing .deb package for first-app.",
    ):
        package_command.sign_package(first_app, identity=JANE)

    # The exported public key is removed after signing.
    assert not public_key_path.exists()


def test_sign_package_key_export_error_in_docker(package_command, first_app, mock_gpg):
    """If the signing key can't be exported, an error is raised and the key file is
    removed."""
    first_app.packaging_format = "deb"
    package_command.distribution_path = mock.MagicMock(
        return_value=Path("/path/to/dist/first-app.deb")
    )
    make_docker_context(package_command, first_app)
    mock_gpg.agent_socket_path.return_value = Path(
        "/run/user/1000/gnupg/S.gpg-agent"
    )
    mock_gpg.export_public_key.side_effect = BriefcaseCommandError("boom")

    public_key_path = package_command.bundle_path(first_app) / "signing-public-key.gpg"
    public_key_path.touch()

    with pytest.raises(BriefcaseCommandError, match=r"boom"):
        package_command.sign_package(first_app, identity=JANE)

    package_command.tools[first_app].app_context.run.assert_not_called()
    assert not public_key_path.exists()
