import subprocess
from pathlib import Path
from unittest import mock

import pytest

from briefcase.exceptions import BriefcaseCommandError
from briefcase.integrations.subprocess import Subprocess
from briefcase.platforms.linux.system import (
    LinuxSystemPackageCommand,
    get_gpg_identities,
)

from ....utils import create_file


@pytest.fixture
def package_command(dummy_console, first_app, tmp_path):
    command = LinuxSystemPackageCommand(
        console=dummy_console,
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )
    command.tools.home_path = tmp_path / "home"

    # Run outside docker for these tests.
    command.target_image = None

    # Mock the detection of system python.
    command.verify_system_python = mock.MagicMock()
    command.verify_system_packages = mock.MagicMock()

    # Mock the packaging tools.
    command._verify_packaging_tools = mock.MagicMock()

    # Mock the GPG identities, so no identities are available by default.
    command.get_gpg_identities = mock.MagicMock(return_value={})

    return command


GPG_OUTPUT = """sec:u:255:22:F9FCBC4A7701B685:1785485940:::u:::scSC:::+::ed25519:::0:
fpr:::::::::5F0B07E0E2D05DD5611BF7A3F9FCBC4A7701B685:
grp:::::::::A93A9F4A002A4796BB0196F46C2ED4F603F95854:
uid:u::::1785485940::E70814C3C8DC3AC3940E8BFBA0288F0CE55F2120::Jane Doe <jane@example.com>::::::::::0:
ssb:u:255:22:5B0C17E0E2D05DD5611BF7A3F9FCBC4A7701B685:1785485940:::u:::e:::+::ed25519:::0:
fpr:::::::::5B0C17E0E2D05DD5611BF7A3F9FCBC4A7701B685:
"""

JANE = "5F0B07E0E2D05DD5611BF7A3F9FCBC4A7701B685"
BOB = "B6C8B38C96FFE1E6A1C66C9F4D68E1A93D2F47FB"


# Tests for the get_gpg_identities() module function.
# ####################################################


def test_get_gpg_identities(package_command):
    """Secret keys are parsed into a dictionary of identities."""
    package_command.tools.subprocess = mock.MagicMock(spec_set=Subprocess)
    package_command.tools.subprocess.check_output.return_value = GPG_OUTPUT

    identities = get_gpg_identities(package_command.tools)

    assert identities == {
        JANE: "Jane Doe <jane@example.com>",
    }
    package_command.tools.subprocess.check_output.assert_called_once_with(
        ["gpg", "--list-secret-keys", "--with-colons"],
        quiet=1,
    )


def test_get_gpg_identities_multiple_keys(package_command):
    """Multiple secret keys are all returned, and subkey fingerprints are ignored."""
    package_command.tools.subprocess = mock.MagicMock(spec_set=Subprocess)
    package_command.tools.subprocess.check_output.return_value = (
        GPG_OUTPUT
        + """sec:u:3072:1:4D68E1A93D2F47FB:1785485980:::u:::scESC:::::::
fpr:::::::::B6C8B38C96FFE1E6A1C66C9F4D68E1A93D2F47FB:
uid:u::::1785485980::89A2D4C6E5F8B3E7::Bob Builder <bob@example.com>::::::::::0:
"""
    )

    identities = get_gpg_identities(package_command.tools)

    assert identities == {
        JANE: "Jane Doe <jane@example.com>",
        BOB: "Bob Builder <bob@example.com>",
    }


def test_get_gpg_identities_multiple_uids(package_command):
    """If a key has multiple user IDs, the first is used."""
    package_command.tools.subprocess = mock.MagicMock(spec_set=Subprocess)
    package_command.tools.subprocess.check_output.return_value = (
        GPG_OUTPUT
        + """uid:u::::1785485940::E70814C3C8DC3AC3940E8BFBA0288F0CE55F2120::Jane <jane@example.com>::::::::::0:
"""
    )

    identities = get_gpg_identities(package_command.tools)

    assert identities == {
        JANE: "Jane Doe <jane@example.com>",
    }


def test_get_gpg_identities_no_keys(package_command):
    """If gpg reports an error (e.g., no secret keys), no identities are returned."""
    package_command.tools.subprocess = mock.MagicMock(spec_set=Subprocess)
    package_command.tools.subprocess.check_output.side_effect = (
        subprocess.CalledProcessError(returncode=2, cmd=["gpg", "--list-secret-keys"])
    )

    assert get_gpg_identities(package_command.tools) == {}


def test_get_gpg_identities_not_installed(package_command):
    """If gpg isn't installed, no identities are returned."""
    package_command.tools.subprocess = mock.MagicMock(spec_set=Subprocess)
    package_command.tools.subprocess.check_output.side_effect = FileNotFoundError(
        "gpg not found"
    )

    assert get_gpg_identities(package_command.tools) == {}


# Tests for select_identity().
# ############################


def test_select_identity_by_fingerprint(package_command):
    """An identity can be selected by full fingerprint."""
    package_command.get_gpg_identities.return_value = {
        JANE: "Jane Doe <jane@example.com>",
        BOB: "Bob Builder <bob@example.com>",
    }

    result = package_command.select_identity(JANE)

    assert result == JANE
    # User input was not solicited
    assert package_command.console.prompts == []


def test_select_identity_by_key_id(package_command):
    """An identity can be selected by key ID (a substring of the fingerprint)."""
    package_command.get_gpg_identities.return_value = {
        JANE: "Jane Doe <jane@example.com>",
        BOB: "Bob Builder <bob@example.com>",
    }

    result = package_command.select_identity("F9FCBC4A7701B685")

    assert result == JANE
    # User input was not solicited
    assert package_command.console.prompts == []


def test_select_identity_by_name(package_command):
    """An identity can be selected by name or email address."""
    package_command.get_gpg_identities.return_value = {
        JANE: "Jane Doe <jane@example.com>",
        BOB: "Bob Builder <bob@example.com>",
    }

    result = package_command.select_identity("jane@example.com")

    assert result == JANE
    # User input was not solicited
    assert package_command.console.prompts == []


def test_select_identity_invalid(package_command):
    """An identity that can't be found raises an error."""
    package_command.get_gpg_identities.return_value = {
        JANE: "Jane Doe <jane@example.com>",
    }

    with pytest.raises(
        BriefcaseCommandError,
        match=r"Invalid signing identity not-an-identity",
    ):
        package_command.select_identity("not-an-identity")

    # User input was not solicited
    assert package_command.console.prompts == []


def test_select_identity_no_identities(package_command):
    """If no identities are available, None is returned."""
    result = package_command.select_identity()

    assert result is None
    # User input was not solicited
    assert package_command.console.prompts == []


def test_select_identity_single(package_command):
    """If only one identity is available, it is used without prompting."""
    package_command.get_gpg_identities.return_value = {
        JANE: "Jane Doe <jane@example.com>",
    }

    result = package_command.select_identity()

    assert result == JANE
    # User input was not solicited
    assert package_command.console.prompts == []


def test_select_identity_multiple(package_command):
    """If multiple identities are available, the user is prompted to select one."""
    package_command.get_gpg_identities.return_value = {
        JANE: "Jane Doe <jane@example.com>",
        BOB: "Bob Builder <bob@example.com>",
    }

    # Select option 1
    package_command.console.values = ["1"]

    result = package_command.select_identity()

    assert result == JANE

    # User input was solicited once
    assert package_command.console.prompts == ["GPG Signing Identity: "]


# Tests for signature_path().
# ###########################


def test_signature_path(package_command, first_app, tmp_path):
    """The signature path is the distribution path plus a .sig suffix."""
    first_app.packaging_format = "pkg"
    package_command.tools[first_app].app_context = mock.MagicMock(spec_set=Subprocess)
    package_command.tools[first_app].app_context.check_output = mock.MagicMock(
        return_value="wonky"
    )

    assert (
        package_command.signature_path(first_app)
        == tmp_path / "base_path/dist/first-app-0.0.1-1-wonky.pkg.tar.zst.sig"
    )


# Tests for _verify_signing_tool().
# #################################


@pytest.mark.parametrize(
    ("format", "tool_name", "package_name"),
    [
        ("deb", "debsigs", "debsigs"),
        ("rpm", "rpmsign", "rpm-sign"),
        ("pkg", "gpg", "gnupg"),
    ],
)
def test_verify_signing_tool_installed(
    package_command,
    first_app,
    format,
    tool_name,
    package_name,
):
    """If the signing tool is installed, no error is raised."""
    first_app.packaging_format = format
    package_command.tools.shutil.which = mock.MagicMock(return_value="/path/to/exe")

    package_command._verify_signing_tool(first_app)


@pytest.mark.parametrize(
    ("format", "tool_name", "package_name"),
    [
        ("deb", "debsigs", "debsigs"),
        ("rpm", "rpmsign", "rpm-sign"),
        ("pkg", "gpg", "gnupg"),
    ],
)
def test_verify_signing_tool_missing(
    package_command,
    first_app,
    format,
    tool_name,
    package_name,
):
    """If the signing tool isn't installed, an error with install hints is raised."""
    first_app.packaging_format = format
    first_app.target_vendor_base = "debian"
    package_command.tools.shutil.which = mock.MagicMock(return_value="")

    with pytest.raises(
        BriefcaseCommandError,
        match=(
            rf"Can't find the {tool_name} tools. "
            rf"Try running `sudo apt install {package_name}`."
        ),
    ):
        package_command._verify_signing_tool(first_app)


def test_verify_signing_tool_missing_unknown_vendor(package_command, first_app):
    """If the signing tool isn't installed on an unknown vendor, a generic error is
    raised."""
    first_app.packaging_format = "deb"
    first_app.target_vendor_base = None
    package_command.tools.shutil.which = mock.MagicMock(return_value="")

    with pytest.raises(
        BriefcaseCommandError,
        match=r"Can't find the debsigs tool. Install this first to sign the deb.",
    ):
        package_command._verify_signing_tool(first_app)


# Tests for sign_package().
# #########################


def test_sign_deb_package(package_command, first_app):
    """A .deb package is signed with debsigs."""
    first_app.packaging_format = "deb"
    package_command.tools.subprocess = mock.MagicMock(spec_set=Subprocess)
    dist_path = Path("/path/to/dist/first-app.deb")
    package_command.distribution_path = mock.MagicMock(return_value=dist_path)

    package_command.sign_package(first_app, identity=JANE)

    package_command.tools.subprocess.run.assert_called_once_with(
        ["debsigs", "--sign=origin", f"--default-key={JANE}", str(dist_path)],
        check=True,
    )


def test_sign_rpm_package(package_command, first_app):
    """A .rpm package is signed with rpmsign."""
    first_app.packaging_format = "rpm"
    package_command.tools.subprocess = mock.MagicMock(spec_set=Subprocess)
    dist_path = Path("/path/to/dist/first-app.rpm")
    package_command.distribution_path = mock.MagicMock(return_value=dist_path)

    package_command.sign_package(first_app, identity=JANE)

    package_command.tools.subprocess.run.assert_called_once_with(
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
    package_command.tools.subprocess = mock.MagicMock(spec_set=Subprocess)
    dist_path = Path("/path/to/dist/first-app.pkg.tar.zst")
    package_command.distribution_path = mock.MagicMock(return_value=dist_path)
    package_command.signature_path = mock.MagicMock(
        return_value=Path("/path/to/dist/first-app.pkg.tar.zst.sig")
    )

    package_command.sign_package(first_app, identity=JANE)

    package_command.tools.subprocess.run.assert_called_once_with(
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
    package_command.tools.subprocess = mock.MagicMock(spec_set=Subprocess)
    package_command.tools.subprocess.run.side_effect = subprocess.CalledProcessError(
        returncode=1, cmd=["debsigs", "--sign=origin", "--default-key=DEADBEEF"]
    )
    package_command.distribution_path = mock.MagicMock(
        return_value=Path("/path/to/dist/first-app.deb")
    )

    with pytest.raises(
        BriefcaseCommandError,
        match=r"Error while signing .deb package for first-app.",
    ):
        package_command.sign_package(first_app, identity=JANE)


# Tests for clean_dist_folder().
# ##############################


def test_clean_dist_folder_removes_signature(package_command, first_app, tmp_path):
    """Cleaning the dist folder also removes the signature file."""
    first_app.packaging_format = "pkg"
    package_command.tools[first_app].app_context = mock.MagicMock(spec_set=Subprocess)
    package_command.tools[first_app].app_context.check_output = mock.MagicMock(
        return_value="wonky"
    )

    dist_path = tmp_path / "base_path/dist/first-app-0.0.1-1-wonky.pkg.tar.zst"
    create_file(dist_path, "package content")
    create_file(Path(f"{dist_path}.sig"), "signature")

    package_command.clean_dist_folder(first_app)

    assert not dist_path.exists()
    assert not Path(f"{dist_path}.sig").exists()


def test_clean_dist_folder_no_signature(package_command, first_app, tmp_path):
    """Cleaning the dist folder when no signature exists is a no-op."""
    first_app.packaging_format = "pkg"
    package_command.tools[first_app].app_context = mock.MagicMock(spec_set=Subprocess)
    package_command.tools[first_app].app_context.check_output = mock.MagicMock(
        return_value="wonky"
    )

    dist_path = tmp_path / "base_path/dist/first-app-0.0.1-1-wonky.pkg.tar.zst"
    create_file(dist_path, "package content")

    package_command.clean_dist_folder(first_app)

    assert not dist_path.exists()


# Tests for package_app().
# ########################


def test_package_app_signs(package_command, first_app):
    """If an identity is available, the package is signed with it."""
    first_app.packaging_format = "deb"
    package_command.get_gpg_identities.return_value = {
        JANE: "Jane Doe <jane@example.com>",
    }
    package_command._package_deb = mock.MagicMock()
    package_command._verify_signing_tool = mock.MagicMock()
    package_command.sign_package = mock.MagicMock()

    package_command.package_app(first_app)

    package_command._package_deb.assert_called_once_with(first_app)
    package_command._verify_signing_tool.assert_called_once_with(first_app)
    package_command.sign_package.assert_called_once_with(first_app, identity=JANE)


def test_package_app_explicit_identity(package_command, first_app):
    """An identity specified on the command line is used to sign the package."""
    first_app.packaging_format = "deb"
    package_command.get_gpg_identities.return_value = {
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
    package_command.get_gpg_identities.return_value = {
        JANE: "Jane Doe <jane@example.com>",
    }
    package_command._package_deb = mock.MagicMock()
    package_command._verify_signing_tool = mock.MagicMock()
    package_command.sign_package = mock.MagicMock()

    package_command.package_app(first_app, adhoc_sign=True)

    package_command._package_deb.assert_called_once_with(first_app)
    package_command._verify_signing_tool.assert_not_called()
    package_command.sign_package.assert_not_called()


def test_package_app_no_identity(package_command, first_app):
    """If no identity is available, the package is not signed."""
    first_app.packaging_format = "deb"
    package_command._package_deb = mock.MagicMock()
    package_command._verify_signing_tool = mock.MagicMock()
    package_command.sign_package = mock.MagicMock()

    package_command.package_app(first_app)

    package_command._package_deb.assert_called_once_with(first_app)
    package_command._verify_signing_tool.assert_not_called()
    package_command.sign_package.assert_not_called()


def test_package_app_invalid_identity(package_command, first_app):
    """An invalid identity raises an error before the package is built."""
    first_app.packaging_format = "deb"
    package_command.get_gpg_identities.return_value = {
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


def test_package_rpm_app_signs(package_command, first_app):
    """An RPM app is signed with the available identity."""
    first_app.packaging_format = "rpm"
    package_command.get_gpg_identities.return_value = {
        JANE: "Jane Doe <jane@example.com>",
    }
    package_command._package_rpm = mock.MagicMock()
    package_command._verify_signing_tool = mock.MagicMock()
    package_command.sign_package = mock.MagicMock()

    package_command.package_app(first_app)

    package_command._package_rpm.assert_called_once_with(first_app)
    package_command._verify_signing_tool.assert_called_once_with(first_app)
    package_command.sign_package.assert_called_once_with(first_app, identity=JANE)


def test_package_pkg_app_signs(package_command, first_app):
    """An Arch app is signed with the available identity."""
    first_app.packaging_format = "pkg"
    package_command.get_gpg_identities.return_value = {
        JANE: "Jane Doe <jane@example.com>",
    }
    package_command._package_pkg = mock.MagicMock()
    package_command._verify_signing_tool = mock.MagicMock()
    package_command.sign_package = mock.MagicMock()

    package_command.package_app(first_app)

    package_command._package_pkg.assert_called_once_with(first_app)
    package_command._verify_signing_tool.assert_called_once_with(first_app)
    package_command.sign_package.assert_called_once_with(first_app, identity=JANE)


def test_package_app_unknown_format_signs(package_command, first_app):
    """An unknown packaging format raises an error, even when signing."""
    first_app.packaging_format = "unknown"
    package_command.get_gpg_identities.return_value = {
        JANE: "Jane Doe <jane@example.com>",
    }
    package_command._package_deb = mock.MagicMock()
    package_command._verify_signing_tool = mock.MagicMock()
    package_command.sign_package = mock.MagicMock()

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


# Tests for the signing option help text.
# #######################################


def test_adhoc_sign_help(package_command):
    """The adhoc sign help text is overridden for Linux."""
    assert package_command.ADHOC_SIGN_HELP == (
        "Perform no signing on the package. If signing is not performed, "
        "users will not be able to verify the provenance of the package."
    )


def test_identity_help(package_command):
    """The identity help text is overridden for Linux."""
    assert package_command.IDENTITY_HELP == (
        "The GPG signing identity to use to sign the package. This can be the "
        "fingerprint, key ID, or the name/email address of any GPG identity "
        "available on the system."
    )
