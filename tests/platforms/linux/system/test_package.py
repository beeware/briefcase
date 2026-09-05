import subprocess
from unittest import mock

import pytest

from briefcase.exceptions import BriefcaseCommandError
from briefcase.integrations.subprocess import Subprocess
from briefcase.platforms.linux.system import LinuxSystemPackageCommand


@pytest.fixture
def package_command(mock_tools, dummy_console, first_app, tmp_path):
    command = LinuxSystemPackageCommand(
        console=dummy_console,
        tools=mock_tools,
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )
    mock_tools.host_os = "Linux"

    # Run outside docker for these tests.
    command.target_image = None

    # Mock the detection of system python.
    command.verify_system_python = mock.MagicMock()
    command.verify_system_packages = mock.MagicMock()

    # Mock the packaging tools.
    command._verify_packaging_tools = mock.MagicMock()

    return command


def test_formats(package_command):
    """The supported packaging formats are as expected."""
    assert package_command.packaging_formats == ["deb", "rpm", "pkg", "system"]


def test_default_format(package_command):
    """No default packaging format is defined; the app configuration determines the
    format."""
    assert package_command.default_packaging_format is None


def test_verify_packaging_tools_unknown_format(package_command, first_app):
    """An unresolved packaging format raises an error naming the vendor."""
    # Restore the real implementation of _verify_packaging_tools
    del package_command._verify_packaging_tools

    first_app.packaging_format = "system"

    with pytest.raises(
        BriefcaseCommandError,
        match=(
            r"Briefcase doesn't know the system packaging format for somevendor. "
            r"You may be able to build a package by manually specifying a format "
            r"with -p/--packaging-format"
        ),
    ):
        package_command._verify_packaging_tools(first_app)


@pytest.mark.parametrize(
    ("format", "vendor", "codename", "revision", "filename"),
    [
        ("rpm", "rhel", "9", None, "first-app-0.0.1-1.el9.wonky.rpm"),
        ("rpm", "rhel", "9", 5, "first-app-0.0.1-5.el9.wonky.rpm"),
        ("rpm", "fedora", "37", None, "first-app-0.0.1-1.fc37.wonky.rpm"),
        (
            "deb",
            "debian",
            "bullseye",
            None,
            "first-app_0.0.1-1~debian-bullseye_wonky.deb",
        ),
        ("deb", "debian", "bullseye", 5, "first-app_0.0.1-5~debian-bullseye_wonky.deb"),
        ("deb", "ubuntu", "jammy", None, "first-app_0.0.1-1~ubuntu-jammy_wonky.deb"),
        (
            "deb",
            "linuxmint",
            "vera",
            None,
            "first-app_0.0.1-1~linuxmint-vera_wonky.deb",
        ),
        ("pkg", "arch", "rolling", None, "first-app-0.0.1-1-wonky.pkg.tar.zst"),
        ("pkg", "manjaro", "rolling", None, "first-app-0.0.1-1-wonky.pkg.tar.zst"),
    ],
)
def test_distribution_path(
    package_command,
    first_app,
    format,
    vendor,
    codename,
    revision,
    filename,
    tmp_path,
):
    first_app.packaging_format = format
    first_app.target_vendor = vendor
    first_app.target_codename = codename

    # Mock return value for ABI from packaging system
    package_command.tools[first_app].app_context = mock.MagicMock(spec_set=Subprocess)
    package_command.tools[first_app].app_context.check_output = mock.MagicMock(
        return_value="wonky"
    )

    if revision:
        first_app.revision = revision

    assert (
        package_command.distribution_path(first_app)
        == tmp_path / "base_path/dist" / filename
    )

    # Confirm ABI was requested from build env
    package_command.tools[first_app].app_context.check_output.assert_called_with(
        {
            "deb": ["dpkg", "--print-architecture"],
            "rpm": ["rpm", "--eval", "%_target_cpu"],
            "pkg": ["pacman-conf", "Architecture"],
        }[format]
    )


@pytest.mark.parametrize("format", ["rpm", "deb", "pkg"])
def test_build_env_abi_failure(package_command, first_app, format):
    """If the subprocess to get the build ABI fails, an error is raised."""
    first_app.packaging_format = format

    # Mock return value for ABI from packaging system
    package_command.tools[first_app].app_context = mock.MagicMock(spec_set=Subprocess)
    package_command.tools[first_app].app_context.check_output = mock.MagicMock(
        side_effect=subprocess.CalledProcessError(returncode=1, cmd="pkg -arch")
    )

    with pytest.raises(
        BriefcaseCommandError,
        match=r"Failed to determine build environment's ABI for packaging\.",
    ):
        getattr(package_command, f"{format}_abi")(first_app)


@pytest.mark.parametrize(
    ("base_vendor", "packaging_format", "expected_requires"),
    [
        # Known formats add the signing tool for that format
        ("debian", "deb", ["debsigs"]),
        ("rhel", "rpm", ["rpm-sign"]),
        ("arch", "pkg", ["gnupg"]),
        # On SUSE, rpmsign is provided by rpm-build; there is no `rpm-sign` package
        ("suse", "rpm", ["rpm-build"]),
    ],
)
def test_docker_packaging_format_adjusts_signing_tools(
    package_command,
    first_app,
    base_vendor,
    packaging_format,
    expected_requires,
):
    """When using Docker, the signing tool is added to the image requirements."""
    first_app.target_vendor_base = base_vendor
    first_app.packaging_format = packaging_format
    package_command.target_image = "somevendor:surprising"
    package_command.extra_docker_build_args = []
    package_command.verify_docker_python = mock.MagicMock()
    package_command.tools[first_app].app_context = mock.MagicMock()

    package_command.verify_app_tools(first_app)

    assert getattr(first_app, "system_requires", []) == expected_requires


def test_docker_packaging_format_signing_tools_are_not_duplicated(
    package_command,
    first_app,
):
    """The signing tool is not added to the image requirements more than once."""
    first_app.target_vendor_base = "debian"
    first_app.packaging_format = "deb"
    package_command.target_image = "somevendor:surprising"
    package_command.extra_docker_build_args = []
    package_command.verify_docker_python = mock.MagicMock()
    package_command.tools[first_app].app_context = mock.MagicMock()

    package_command.verify_app_tools(first_app)
    package_command.verify_app_tools(first_app)

    assert first_app.system_requires == ["debsigs"]


def test_native_packaging_does_not_add_signing_tools(package_command, first_app):
    """The signing tool is not added to the host requirements when not using Docker."""
    first_app.target_vendor_base = "debian"
    first_app.packaging_format = "deb"

    package_command.verify_app_tools(first_app)

    assert getattr(first_app, "system_requires", None) is None


def test_package_deb_app(package_command, first_app, mock_gpg):
    """A debian app can be packaged."""
    # Set the packaging format
    first_app.packaging_format = "deb"

    # Mock the actual packaging call
    package_command._package_deb = mock.MagicMock()

    # Accept the default selection ("Don't sign")
    package_command.console.values = [""]

    # Package the app
    package_command.package_app(first_app)

    # Assert the right backend was called.
    package_command._package_deb.assert_called_once_with(first_app)


def test_package_rpm_app(package_command, first_app, mock_gpg):
    """A Red Hat app can be packaged."""
    # Set the packaging format
    first_app.packaging_format = "rpm"

    # Mock the actual packaging call
    package_command._package_rpm = mock.MagicMock()

    # Accept the default selection ("Don't sign")
    package_command.console.values = [""]

    # Package the app
    package_command.package_app(first_app)

    # Assert the right backend was called.
    package_command._package_rpm.assert_called_once_with(first_app)


def test_package_pkg_app(package_command, first_app, mock_gpg):
    """An Arch app can be packaged."""
    # Set the packaging format
    first_app.packaging_format = "pkg"

    # Mock the actual packaging call
    package_command._package_pkg = mock.MagicMock()

    # Accept the default selection ("Don't sign")
    package_command.console.values = [""]

    # Package the app
    package_command.package_app(first_app)

    # Assert the right backend was called.
    package_command._package_pkg.assert_called_once_with(first_app)


def test_package_unknown_format(package_command, first_app, mock_gpg):
    """Unknown/unsupported packaging formats raise an error."""
    # Set the packaging format
    first_app.packaging_format = "unknown"

    # Mock the actual packaging call
    package_command._package_deb = mock.MagicMock()

    # Accept the default selection ("Don't sign")
    package_command.console.values = [""]

    # Package the app
    with pytest.raises(
        BriefcaseCommandError,
        match=(
            r"Briefcase doesn't currently know "
            r"how to build system packages in UNKNOWN format."
        ),
    ):
        package_command.package_app(first_app)
