import subprocess
from unittest import mock

import pytest

from briefcase.console import Console, Log
from briefcase.exceptions import BriefcaseCommandError
from briefcase.integrations.subprocess import Subprocess
from briefcase.platforms.linux.system import LinuxSystemPackageCommand


@pytest.fixture
def package_command(monkeypatch, first_app, tmp_path):
    command = LinuxSystemPackageCommand(
        logger=Log(),
        console=Console(),
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

    return command


def test_formats(package_command):
    """The supported packaging formats are as expected."""
    assert package_command.packaging_formats == ["deb", "rpm", "pkg", "system"]


@pytest.mark.parametrize(
    "format, vendor, codename, revision, filename",
    [
        ["rpm", "rhel", "9", None, "first-app-0.0.1-1.el9.wonky.rpm"],
        ["rpm", "rhel", "9", 5, "first-app-0.0.1-5.el9.wonky.rpm"],
        ["rpm", "fedora", "37", None, "first-app-0.0.1-1.fc37.wonky.rpm"],
        [
            "deb",
            "debian",
            "bullseye",
            None,
            "first-app_0.0.1-1~debian-bullseye_wonky.deb",
        ],
        ["deb", "debian", "bullseye", 5, "first-app_0.0.1-5~debian-bullseye_wonky.deb"],
        ["deb", "ubuntu", "jammy", None, "first-app_0.0.1-1~ubuntu-jammy_wonky.deb"],
        [
            "deb",
            "linuxmint",
            "vera",
            None,
            "first-app_0.0.1-1~linuxmint-vera_wonky.deb",
        ],
        ["pkg", "arch", "rolling", None, "first-app-0.0.1-1-wonky.pkg.tar.zst"],
        ["pkg", "manjaro", "rolling", None, "first-app-0.0.1-1-wonky.pkg.tar.zst"],
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
        match="Failed to determine build environment's ABI for packaging.",
    ):
        getattr(package_command, f"{format}_abi")(first_app)


@pytest.mark.parametrize(
    "base_vendor, input_format, output_format",
    [
        # System packaging maps to known formats
        ("debian", "system", "deb"),
        ("rhel", "system", "rpm"),
        ("arch", "system", "pkg"),
        # Explicit output format is preserved
        ("debian", "deb", "deb"),
        ("redhat", "rpm", "rpm"),
        ("arch", "pkg", "pkg"),
        # This is technically possible, but probably ill-advised
        ("debian", "rpm", "rpm"),
        # Unknown base vendor, but explicit packaging format
        (None, "deb", "deb"),
        (None, "rpm", "rpm"),
        (None, "pkg", "pkg"),
    ],
)
def test_adjust_packaging_format(
    package_command,
    first_app,
    base_vendor,
    input_format,
    output_format,
):
    """The packaging format can be adjusted based on host system knowledge."""
    first_app.target_vendor_base = base_vendor
    first_app.packaging_format = input_format

    package_command.verify_app_tools(first_app)

    assert first_app.packaging_format == output_format


def test_unknown_packaging_format(package_command, first_app):
    """An unknown packaging format raises an error."""
    first_app.target_vendor_base = None
    first_app.packaging_format = "system"

    with pytest.raises(
        BriefcaseCommandError,
        match=r"Briefcase doesn't know the system packaging format for somevendor.",
    ):
        package_command.verify_app_tools(first_app)


def test_package_deb_app(package_command, first_app):
    """A debian app can be packaged."""
    # Set the packaging format
    first_app.packaging_format = "deb"

    # Mock the actual packaging call
    package_command._package_deb = mock.MagicMock()

    # Package the app
    package_command.package_app(first_app)

    # Assert the right backend was called.
    package_command._package_deb.assert_called_once_with(first_app)


def test_package_rpm_app(package_command, first_app):
    """A Red Hat app can be packaged."""
    # Set the packaging format
    first_app.packaging_format = "rpm"

    # Mock the actual packaging call
    package_command._package_rpm = mock.MagicMock()

    # Package the app
    package_command.package_app(first_app)

    # Assert the right backend was called.
    package_command._package_rpm.assert_called_once_with(first_app)


def test_package_pkg_app(package_command, first_app):
    """An Arch app can be packaged."""
    # Set the packaging format
    first_app.packaging_format = "pkg"

    # Mock the actual packaging call
    package_command._package_pkg = mock.MagicMock()

    # Package the app
    package_command.package_app(first_app)

    # Assert the right backend was called.
    package_command._package_pkg.assert_called_once_with(first_app)


def test_package_unknown_format(package_command, first_app):
    """Unknown/unsupported packaging formats raise an error."""
    # Set the packaging format
    first_app.packaging_format = "unknown"

    # Mock the actual packaging call
    package_command._package_deb = mock.MagicMock()

    # Package the app
    with pytest.raises(
        BriefcaseCommandError,
        match=r"Briefcase doesn't currently know how to build system packages in UNKNOWN format.",
    ):
        package_command.package_app(first_app)
