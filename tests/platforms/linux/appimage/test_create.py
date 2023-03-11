import pytest

from briefcase.console import Console, Log
from briefcase.exceptions import UnsupportedHostError
from briefcase.platforms.linux.appimage import LinuxAppImageCreateCommand


@pytest.fixture
def create_command(first_app_config, tmp_path):
    return LinuxAppImageCreateCommand(
        logger=Log(),
        console=Console(),
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )


def test_default_options(create_command):
    """The default options are as expected."""
    options = create_command.parse_options([])

    assert options == {}

    assert create_command.use_docker


def test_options(create_command):
    """The extra options can be parsed."""
    options = create_command.parse_options(["--no-docker"])

    assert options == {}

    assert not create_command.use_docker


@pytest.mark.parametrize("host_os", ["Windows", "WeirdOS"])
def test_unsupported_host_os_with_docker(create_command, host_os):
    """Error raised for an unsupported OS when using Docker."""
    create_command.use_docker = True
    create_command.tools.host_os = host_os

    with pytest.raises(
        UnsupportedHostError,
        match="Linux AppImages can only be built on Linux, or on macOS using Docker.",
    ):
        create_command()


@pytest.mark.parametrize("host_os", ["Darwin", "Windows", "WeirdOS"])
def test_unsupported_host_os_without_docker(
    create_command,
    host_os,
):
    """Error raised for an unsupported OS when not using Docker."""
    create_command.use_docker = False
    create_command.tools.host_os = host_os

    with pytest.raises(
        UnsupportedHostError,
        match="Linux AppImages can only be built on Linux, or on macOS using Docker.",
    ):
        create_command()


def test_finalize_docker(create_command, first_app_config, capsys):
    """No warning is generated when building an AppImage in Docker."""
    create_command.use_docker = True

    create_command.finalize_app_config(first_app_config)

    # Warning message was not recorded
    assert "WARNING: Building a Local AppImage!" not in capsys.readouterr().out


def test_finalize_nodocker(create_command, first_app_config, capsys):
    """A warning is generated when building an AppImage outside Docker."""
    create_command.use_docker = False

    create_command.finalize_app_config(first_app_config)

    # Warning message was not recorded
    assert "WARNING: Building a Local AppImage!" in capsys.readouterr().out


@pytest.mark.parametrize(
    "manylinux, host_arch, context",
    [
        # Fallback.
        (None, "x86_64", {}),
        # x86_64 architecture, all tags
        (
            "manylinux1",
            "x86_64",
            {"manylinux_tag": "manylinux1_x86_64", "vendor_base": "centos"},
        ),
        (
            "manylinux2010",
            "x86_64",
            {"manylinux_tag": "manylinux2010_x86_64", "vendor_base": "centos"},
        ),
        (
            "manylinux2014",
            "x86_64",
            {"manylinux_tag": "manylinux2014_x86_64", "vendor_base": "centos"},
        ),
        (
            "manylinux_2_24",
            "x86_64",
            {"manylinux_tag": "manylinux_2_24_x86_64", "vendor_base": "debian"},
        ),
        (
            "manylinux_2_28",
            "x86_64",
            {"manylinux_tag": "manylinux_2_28_x86_64", "vendor_base": "almalinux"},
        ),
        # non x86 architecture
        (
            "manylinux2014",
            "aarch64",
            {"manylinux_tag": "manylinux2014_aarch64", "vendor_base": "centos"},
        ),
    ],
)
def test_output_format_template_context(
    create_command, first_app_config, manylinux, host_arch, context
):
    """The template context reflects the manylinux tag and architecture"""
    if manylinux:
        first_app_config.manylinux = manylinux

    create_command.tools.host_arch = host_arch

    assert create_command.output_format_template_context(first_app_config) == context
