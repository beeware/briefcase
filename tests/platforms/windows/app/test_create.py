import sys

import pytest

from briefcase.console import Console, Log
from briefcase.exceptions import UnsupportedHostError
from briefcase.platforms.windows.app import WindowsAppCreateCommand


@pytest.fixture
def create_command(tmp_path):
    return WindowsAppCreateCommand(
        logger=Log(),
        console=Console(),
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )


@pytest.mark.parametrize("host_os", ["Darwin", "Linux", "WeirdOS"])
def test_unsupported_host_os(create_command, host_os):
    """Error raised for an unsupported OS."""
    create_command.tools.host_os = host_os

    with pytest.raises(
        UnsupportedHostError,
        match="Windows applications can only be built on Windows.",
    ):
        create_command()


@pytest.mark.parametrize("host_arch", ["i686", "ARM64", "wonky"])
def test_unsupported_arch(create_command, host_arch):
    """Windows commands can only run on x86-64."""
    create_command.tools.host_os = "Windows"
    create_command.tools.host_arch = host_arch

    with pytest.raises(
        UnsupportedHostError,
        match=f"Windows applications cannot be built on an {host_arch} machine.",
    ):
        create_command()


def test_supported_arch(create_command):
    """Windows command are allowed to run on x86-64."""
    create_command.tools.host_os = "Windows"
    create_command.tools.host_arch = "AMD64"

    create_command()


def test_unsupported_32bit_python(create_command):
    """Windows commands cannot run with 32bit Python."""
    create_command.tools.host_os = "Windows"
    create_command.tools.host_arch = "AMD64"
    create_command.tools.is_32bit_python = True

    with pytest.raises(
        UnsupportedHostError,
        match="Windows applications cannot be built using a 32bit version of Python",
    ):
        create_command()


@pytest.mark.parametrize(
    "version, version_triple",
    [
        ("1", "1.0.0"),
        ("1.2", "1.2.0"),
        ("1.2.3", "1.2.3"),
        ("1.2.3.4", "1.2.3"),
        ("1.2.3a4", "1.2.3"),
        ("1.2.3b5", "1.2.3"),
        ("1.2.3rc6", "1.2.3"),
        ("1.2.3.dev7", "1.2.3"),
        ("1.2.3.post8", "1.2.3"),
    ],
)
def test_version_triple(
    create_command, first_app_config, tmp_path, version, version_triple
):
    first_app_config.version = version
    context = create_command.output_format_template_context(first_app_config)

    assert context["version_triple"] == version_triple


def test_explicit_version_triple(create_command, first_app_config, tmp_path):
    first_app_config.version = "1.2.3a1"
    first_app_config.version_triple = "2.3.4"

    context = create_command.output_format_template_context(first_app_config)

    # Explicit version triple is used.
    assert context["version_triple"] == "2.3.4"


def test_guid(create_command, first_app_config, tmp_path):
    """A predictable GUID will be generated from the bundle."""
    context = create_command.output_format_template_context(first_app_config)

    assert context["guid"] == "d666a4f1-c7b7-52cc-888a-3a35a7cc97e5"


def test_explicit_guid(create_command, first_app_config, tmp_path):
    """If a GUID is explicitly provided, it is used."""
    first_app_config.guid = "e822176f-b755-589f-849c-6c6600f7efb1"
    context = create_command.output_format_template_context(first_app_config)

    # Explicitly provided GUID is used.
    assert context["guid"] == "e822176f-b755-589f-849c-6c6600f7efb1"


def test_support_package_url(create_command, first_app_config, tmp_path):
    """A valid support package URL is created for a support revision."""
    revision = 5
    expected_link = (
        f"https://www.python.org/ftp/python"
        f"/{sys.version_info.major}.{sys.version_info.minor}.{revision}"
        f"/python-{sys.version_info.major}.{sys.version_info.minor}.{revision}-embed-amd64.zip"
    )
    assert create_command.support_package_url(revision) == expected_link


def test_default_install_scope(create_command, first_app_config, tmp_path):
    """By default, app should be installed per user."""
    context = create_command.output_format_template_context(first_app_config)

    assert context == {
        "guid": "d666a4f1-c7b7-52cc-888a-3a35a7cc97e5",
        "version_triple": "0.0.1",
        "install_scope": None,
    }


def test_per_machine_install_scope(create_command, first_app_config, tmp_path):
    """By default, app should be installed per user."""
    first_app_config.system_installer = True

    context = create_command.output_format_template_context(first_app_config)

    assert context == {
        "guid": "d666a4f1-c7b7-52cc-888a-3a35a7cc97e5",
        "version_triple": "0.0.1",
        "install_scope": "perMachine",
    }


def test_per_user_install_scope(create_command, first_app_config, tmp_path):
    """App can be set to have explicit per-user scope."""
    first_app_config.system_installer = False

    context = create_command.output_format_template_context(first_app_config)

    assert context == {
        "guid": "d666a4f1-c7b7-52cc-888a-3a35a7cc97e5",
        "version_triple": "0.0.1",
        "install_scope": "perUser",
    }
