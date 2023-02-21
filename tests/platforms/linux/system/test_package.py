from unittest import mock

import pytest

from briefcase.console import Console, Log
from briefcase.exceptions import BriefcaseCommandError
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

    # Set the host architecture for test purposes.
    command.tools.host_arch = "wonky"

    # Run outside docker for these tests.
    command.target_image = None

    # Mock the detection of system python.
    command.verify_system_python = mock.MagicMock()

    # Mock the debian packaging tools.
    command._verify_deb_tools = mock.MagicMock()

    return command


def test_formats(package_command):
    "The supported packaging formats are as expected."
    assert package_command.packaging_formats == ["deb", "rpm", "pkg", "system"]


@pytest.mark.parametrize(
    "base_vendor, input_format, output_format",
    [
        # System packaging maps to known formats
        ("debian", "system", "deb"),
        ("redhat", "system", "rpm"),
        ("archlinux", "system", "pkg"),
        # Explicit output format is preserved
        ("debian", "deb", "deb"),
        ("redhat", "rpm", "rpm"),
        ("archlinux", "pkg", "pkg"),
        # This is technically posssible, but probably ill-advised
        ("debian", "rpm", "rpm"),
        # Unknown base vendor, but explicit packaging format
        (None, "deb", "deb"),
        (None, "rpm", "rpm"),
        (None, "pkg", "pkg"),
    ],
)
def test_adjust_packaging_format(
    package_command, first_app, base_vendor, input_format, output_format
):
    "The packaging format can be ajusted based on host system knowledge"
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
    """A debian app can be packaged"""
    # Set the packaging format
    first_app.packaging_format = "deb"

    # Mock the actual packaging call
    package_command._package_deb = mock.MagicMock()

    # Package the app
    package_command.package_app(first_app)

    # Assert the right backend was called.
    package_command._package_deb.assert_called_once_with(first_app)


def test_package_unknown_format(package_command, first_app):
    "Unknown/unsupported packaging formats raise an error"
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
