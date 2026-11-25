from unittest import mock

import pytest

from briefcase.exceptions import BriefcaseCommandError

from .conftest import BOB, JANE


def test_package_app_signs(package_command, first_app, mock_gpg):
    """If an identity is available, the package is signed with it."""
    first_app.packaging_format = "deb"
    mock_gpg.identities.return_value = {
        JANE: "Jane Doe <jane@example.com>",
    }
    package_command._package_deb = mock.MagicMock()
    package_command._verify_signing_tool = mock.MagicMock()
    package_command.sign_package = mock.MagicMock()
    # Accept the default selection (the single available identity)
    package_command.console.values = [""]

    package_command.package_app(first_app)

    package_command._package_deb.assert_called_once_with(first_app)
    package_command._verify_signing_tool.assert_called_once_with(first_app)
    package_command.sign_package.assert_called_once_with(first_app, identity=JANE)


def test_package_app_explicit_identity(package_command, first_app, mock_gpg):
    """An identity specified on the command line is used to sign the package."""
    first_app.packaging_format = "deb"
    mock_gpg.identities.return_value = {
        JANE: "Jane Doe <jane@example.com>",
        BOB: "Bob Builder <bob@example.com>",
    }
    package_command._package_deb = mock.MagicMock()
    package_command._verify_signing_tool = mock.MagicMock()
    package_command.sign_package = mock.MagicMock()

    package_command.package_app(first_app, identity="jane@example.com")

    package_command._package_deb.assert_called_once_with(first_app)
    package_command._verify_signing_tool.assert_called_once_with(first_app)
    package_command.sign_package.assert_called_once_with(first_app, identity=JANE)


def test_package_app_adhoc_sign(package_command, first_app):
    """adhoc_sign means the package is not signed."""
    first_app.packaging_format = "deb"
    package_command._package_deb = mock.MagicMock()
    package_command._verify_signing_tool = mock.MagicMock()
    package_command.sign_package = mock.MagicMock()

    package_command.package_app(first_app, adhoc_sign=True)

    package_command._package_deb.assert_called_once_with(first_app)
    package_command._verify_signing_tool.assert_not_called()
    package_command.sign_package.assert_not_called()


def test_package_app_no_identity(package_command, first_app, mock_gpg):
    """If no identity is available, the package is not signed."""
    first_app.packaging_format = "deb"
    package_command._package_deb = mock.MagicMock()
    package_command._verify_signing_tool = mock.MagicMock()
    package_command.sign_package = mock.MagicMock()
    # Accept the default selection ("Don't sign")
    package_command.console.values = [""]

    package_command.package_app(first_app)

    package_command._package_deb.assert_called_once_with(first_app)
    package_command._verify_signing_tool.assert_not_called()
    package_command.sign_package.assert_not_called()


def test_package_app_dont_sign(package_command, first_app, mock_gpg):
    """If the user opts out of signing from the menu, the package is not signed."""
    first_app.packaging_format = "deb"
    mock_gpg.identities.return_value = {
        JANE: "Jane Doe <jane@example.com>",
        BOB: "Bob Builder <bob@example.com>",
    }
    package_command._package_deb = mock.MagicMock()
    package_command._verify_signing_tool = mock.MagicMock()
    package_command.sign_package = mock.MagicMock()
    # Select option 1 ("Don't sign")
    package_command.console.values = ["1"]

    package_command.package_app(first_app)

    package_command._package_deb.assert_called_once_with(first_app)
    package_command._verify_signing_tool.assert_not_called()
    package_command.sign_package.assert_not_called()


def test_package_app_invalid_identity(package_command, first_app, mock_gpg):
    """An invalid identity raises an error before the package is built."""
    first_app.packaging_format = "deb"
    mock_gpg.identities.return_value = {
        JANE: "Jane Doe <jane@example.com>",
    }
    package_command._package_deb = mock.MagicMock()
    package_command._verify_signing_tool = mock.MagicMock()
    package_command.sign_package = mock.MagicMock()

    with pytest.raises(
        BriefcaseCommandError,
        match=r"Invalid signing identity not-an-identity",
    ):
        package_command.package_app(first_app, identity="not-an-identity")

    package_command._package_deb.assert_not_called()
    package_command._verify_signing_tool.assert_not_called()
    package_command.sign_package.assert_not_called()


def test_package_rpm_app_signs(package_command, first_app, mock_gpg):
    """An RPM app is signed with the available identity."""
    first_app.packaging_format = "rpm"
    mock_gpg.identities.return_value = {
        JANE: "Jane Doe <jane@example.com>",
    }
    package_command._package_rpm = mock.MagicMock()
    package_command._verify_signing_tool = mock.MagicMock()
    package_command.sign_package = mock.MagicMock()
    # Accept the default selection (the single available identity)
    package_command.console.values = [""]

    package_command.package_app(first_app)

    package_command._package_rpm.assert_called_once_with(first_app)
    package_command._verify_signing_tool.assert_called_once_with(first_app)
    package_command.sign_package.assert_called_once_with(first_app, identity=JANE)


def test_package_pkg_app_signs(package_command, first_app, mock_gpg):
    """An Arch app is signed with the available identity."""
    first_app.packaging_format = "pkg"
    mock_gpg.identities.return_value = {
        JANE: "Jane Doe <jane@example.com>",
    }
    package_command._package_pkg = mock.MagicMock()
    package_command._verify_signing_tool = mock.MagicMock()
    package_command.sign_package = mock.MagicMock()
    # Accept the default selection (the single available identity)
    package_command.console.values = [""]

    package_command.package_app(first_app)

    package_command._package_pkg.assert_called_once_with(first_app)
    package_command._verify_signing_tool.assert_called_once_with(first_app)
    package_command.sign_package.assert_called_once_with(first_app, identity=JANE)


def test_package_app_unknown_format_signs(package_command, first_app, mock_gpg):
    """An unknown packaging format raises an error, even when signing."""
    first_app.packaging_format = "unknown"
    mock_gpg.identities.return_value = {
        JANE: "Jane Doe <jane@example.com>",
    }
    package_command._package_deb = mock.MagicMock()
    package_command._verify_signing_tool = mock.MagicMock()
    package_command.sign_package = mock.MagicMock()
    # Accept the default selection (the single available identity)
    package_command.console.values = [""]

    with pytest.raises(
        BriefcaseCommandError,
        match=(
            r"Briefcase doesn't currently know how to build system packages "
            r"in UNKNOWN format."
        ),
    ):
        package_command.package_app(first_app)

    package_command._package_deb.assert_not_called()
    package_command._verify_signing_tool.assert_called_once_with(first_app)
    package_command.sign_package.assert_not_called()


def test_package_app_signs_in_docker(
    package_command,
    first_app,
    mock_gpg,
):
    """If an identity is available, a Docker build is signed with it."""
    first_app.packaging_format = "deb"
    mock_gpg.identities.return_value = {
        JANE: "Jane Doe <jane@example.com>",
    }
    package_command._package_deb = mock.MagicMock()
    package_command._verify_signing_tool = mock.MagicMock()
    package_command.sign_package = mock.MagicMock()
    package_command.target_image = "debian:bookworm"
    # Accept the default selection (the single available identity)
    package_command.console.values = [""]

    package_command.package_app(first_app)

    package_command._package_deb.assert_called_once_with(first_app)
    package_command._verify_signing_tool.assert_called_once_with(first_app)
    package_command.sign_package.assert_called_once_with(first_app, identity=JANE)


def test_package_app_explicit_identity_in_docker(
    package_command,
    first_app,
    mock_gpg,
):
    """An explicit identity is used to sign a Docker build."""
    first_app.packaging_format = "deb"
    mock_gpg.identities.return_value = {
        JANE: "Jane Doe <jane@example.com>",
        BOB: "Bob Builder <bob@example.com>",
    }
    package_command._package_deb = mock.MagicMock()
    package_command._verify_signing_tool = mock.MagicMock()
    package_command.sign_package = mock.MagicMock()
    package_command.target_image = "debian:bookworm"

    package_command.package_app(first_app, identity="jane@example.com")

    package_command._package_deb.assert_called_once_with(first_app)
    package_command._verify_signing_tool.assert_called_once_with(first_app)
    package_command.sign_package.assert_called_once_with(first_app, identity=JANE)


def test_package_app_dont_sign_in_docker(package_command, first_app, mock_gpg):
    """A Docker build is permitted if the user opts out of signing."""
    first_app.packaging_format = "deb"
    mock_gpg.identities.return_value = {
        JANE: "Jane Doe <jane@example.com>",
        BOB: "Bob Builder <bob@example.com>",
    }
    package_command._package_deb = mock.MagicMock()
    package_command._verify_signing_tool = mock.MagicMock()
    package_command.sign_package = mock.MagicMock()
    package_command.target_image = "debian:bookworm"
    # Select option 1 ("Don't sign")
    package_command.console.values = ["1"]

    package_command.package_app(first_app)

    package_command._package_deb.assert_called_once_with(first_app)
    package_command._verify_signing_tool.assert_not_called()
    package_command.sign_package.assert_not_called()


def test_package_app_adhoc_sign_in_docker(package_command, first_app):
    """A Docker build is permitted with adhoc signing."""
    first_app.packaging_format = "deb"
    package_command._package_deb = mock.MagicMock()
    package_command._verify_signing_tool = mock.MagicMock()
    package_command.sign_package = mock.MagicMock()
    package_command.target_image = "debian:bookworm"

    package_command.package_app(first_app, adhoc_sign=True)

    package_command._package_deb.assert_called_once_with(first_app)
    package_command._verify_signing_tool.assert_not_called()
    package_command.sign_package.assert_not_called()
