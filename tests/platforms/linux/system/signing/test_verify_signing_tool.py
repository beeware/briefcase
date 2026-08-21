import subprocess
from unittest import mock

import pytest

from briefcase.exceptions import BriefcaseCommandError


@pytest.mark.parametrize("format", ["deb", "rpm"])
def test_verify_signing_tool_installed(package_command, first_app, format):
    """If the signing tool is installed, no error is raised."""
    first_app.packaging_format = format

    package_command._verify_signing_tool(first_app)

    executable_name = {"deb": "debsigs", "rpm": "rpmsign"}[format]
    package_command.tools[first_app].app_context.check_output.assert_called_once_with(
        ["sh", "-c", f"command -v {executable_name}"],
        quiet=1,
    )


@pytest.mark.parametrize(
    ("format", "tool_name", "package_name"),
    [
        ("deb", "debsigs", "debsigs"),
        ("rpm", "rpmsign", "rpm-sign"),
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
    package_command.tools[
        first_app
    ].app_context.check_output.side_effect = subprocess.CalledProcessError(
        returncode=1,
        cmd=["sh", "-c", f"command -v {tool_name}"],
    )

    with pytest.raises(
        BriefcaseCommandError,
        match=(
            rf"Can't find the {tool_name} tools. "
            rf"Try running `sudo apt install {package_name}`. "
            r"Alternatively, use `--adhoc-sign` to skip signing the package."
        ),
    ):
        package_command._verify_signing_tool(first_app)


def test_verify_signing_tool_missing_unknown_vendor(package_command, first_app):
    """If the signing tool isn't installed on an unknown vendor, a generic error is
    raised."""
    first_app.packaging_format = "deb"
    first_app.target_vendor_base = None
    package_command.tools[
        first_app
    ].app_context.check_output.side_effect = subprocess.CalledProcessError(
        returncode=1,
        cmd=["sh", "-c", "command -v debsigs"],
    )

    with pytest.raises(
        BriefcaseCommandError,
        match=(
            r"Can't find the debsigs tool. Install this first to sign the deb. "
            r"Alternatively, use `--adhoc-sign` to skip signing the package."
        ),
    ):
        package_command._verify_signing_tool(first_app)


def test_verify_signing_tool_pkg(package_command, first_app):
    """For pkg format, the gpg tool is verified through the GnuPG tool."""
    first_app.packaging_format = "pkg"

    with mock.patch("briefcase.platforms.linux.system.GnuPG.verify") as verify:
        package_command._verify_signing_tool(first_app)

    verify.assert_called_once_with(tools=package_command.tools)
