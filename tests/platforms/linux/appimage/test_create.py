import pytest

from briefcase.console import Console, Log
from briefcase.exceptions import BriefcaseConfigError, UnsupportedHostError
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
    "manylinux, tag, host_arch, context",
    [
        # Fallback.
        (None, None, "x86_64", {}),
        # x86_64 architecture, all versions
        # Explicit tag
        (
            "manylinux1",
            "2023-03-05-271004f",
            "x86_64",
            {
                "manylinux_image": "manylinux1_x86_64:2023-03-05-271004f",
                "vendor_base": "centos",
            },
        ),
        # Explicit latest
        (
            "manylinux2010",
            "latest",
            "x86_64",
            {"manylinux_image": "manylinux2010_x86_64:latest", "vendor_base": "centos"},
        ),
        # Implicit latest
        (
            "manylinux2014",
            None,
            "x86_64",
            {"manylinux_image": "manylinux2014_x86_64:latest", "vendor_base": "centos"},
        ),
        (
            "manylinux_2_24",
            None,
            "x86_64",
            {
                "manylinux_image": "manylinux_2_24_x86_64:latest",
                "vendor_base": "debian",
            },
        ),
        (
            "manylinux_2_28",
            None,
            "x86_64",
            {
                "manylinux_image": "manylinux_2_28_x86_64:latest",
                "vendor_base": "almalinux",
            },
        ),
        # non x86 architecture
        (
            "manylinux2014",
            None,
            "aarch64",
            {
                "manylinux_image": "manylinux2014_aarch64:latest",
                "vendor_base": "centos",
            },
        ),
    ],
)
def test_output_format_template_context(
    create_command, first_app_config, manylinux, tag, host_arch, context
):
    """The template context reflects the manylinux name, tag and architecture."""
    if manylinux:
        first_app_config.manylinux = manylinux
    if tag:
        first_app_config.manylinux_image_tag = tag

    create_command.tools.host_arch = host_arch

    assert create_command.output_format_template_context(first_app_config) == context


def test_output_format_template_context_bad_tag(create_command, first_app_config):
    """An unknown manylinux tag raises an error."""
    first_app_config.manylinux = "unknown"
    with pytest.raises(BriefcaseConfigError, match=r"Unknown manylinux tag 'unknown'"):
        assert create_command.output_format_template_context(first_app_config)
