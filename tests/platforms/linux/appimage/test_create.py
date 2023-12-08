from unittest.mock import MagicMock

import pytest

from briefcase.console import Console, Log
from briefcase.exceptions import BriefcaseConfigError, UnsupportedHostError
from briefcase.platforms.linux.appimage import LinuxAppImageCreateCommand


@pytest.fixture
def create_command(first_app_config, tmp_path):
    command = LinuxAppImageCreateCommand(
        logger=Log(),
        console=Console(),
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )
    command.tools.host_arch = "x86_64"
    return command


def test_default_options(create_command):
    """The default options are as expected."""
    options, overrides = create_command.parse_options([])

    assert options == {}
    assert overrides == {}

    assert create_command.use_docker


def test_options(create_command):
    """The extra options can be parsed."""
    options, overrides = create_command.parse_options(["--no-docker"])

    assert options == {}
    assert overrides == {}

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
def test_unsupported_host_os_without_docker(create_command, host_os):
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

    stdout = capsys.readouterr().out
    # Warning message was not recorded
    assert "WARNING: Building a Local AppImage!" not in stdout

    # Generic appimage warning *was* recorded
    assert "WARNING: Use of AppImage is not recommended!" in stdout


def test_finalize_nodocker(create_command, first_app_config, capsys):
    """A warning is generated when building an AppImage outside Docker."""
    create_command.use_docker = False

    create_command.finalize_app_config(first_app_config)

    stdout = capsys.readouterr().out
    # Warning message was recorded
    assert "WARNING: Building a Local AppImage!" in stdout

    # Generic appimage warning *was* recorded
    assert "WARNING: Use of AppImage is not recommended!" in stdout


@pytest.mark.parametrize(
    "manylinux, tag, host_os, host_arch, is_user_mapped, context",
    [
        # Fallback.
        (None, None, "Linux", "x86_64", False, {"use_non_root_user": True}),
        # Linux on x86_64 architecture, all versions
        # Explicit tag
        (
            "manylinux1",
            "2023-03-05-271004f",
            "Linux",
            "x86_64",
            True,
            {
                "manylinux_image": "manylinux1_x86_64:2023-03-05-271004f",
                "vendor_base": "centos",
                "use_non_root_user": False,
            },
        ),
        # Explicit latest
        (
            "manylinux2010",
            "latest",
            "Linux",
            "x86_64",
            False,
            {
                "manylinux_image": "manylinux2010_x86_64:latest",
                "vendor_base": "centos",
                "use_non_root_user": True,
            },
        ),
        # Implicit latest
        (
            "manylinux2014",
            None,
            "Linux",
            "x86_64",
            True,
            {
                "manylinux_image": "manylinux2014_x86_64:latest",
                "vendor_base": "centos",
                "use_non_root_user": False,
            },
        ),
        (
            "manylinux_2_24",
            None,
            "Linux",
            "x86_64",
            True,
            {
                "manylinux_image": "manylinux_2_24_x86_64:latest",
                "vendor_base": "debian",
                "use_non_root_user": False,
            },
        ),
        (
            "manylinux_2_28",
            None,
            "Linux",
            "x86_64",
            False,
            {
                "manylinux_image": "manylinux_2_28_x86_64:latest",
                "vendor_base": "almalinux",
                "use_non_root_user": True,
            },
        ),
        # Linux on i686 hardware
        (
            "manylinux_2_28",
            None,
            "Linux",
            "i686",
            False,
            {
                "manylinux_image": "manylinux_2_28_i686:latest",
                "vendor_base": "almalinux",
                "use_non_root_user": True,
            },
        ),
        # Linux on aarch64 hardware
        (
            "manylinux_2_28",
            None,
            "Linux",
            "aarch64",
            False,
            {
                "manylinux_image": "manylinux_2_28_aarch64:latest",
                "vendor_base": "almalinux",
                "use_non_root_user": True,
            },
        ),
        # Linux on arm hardware
        (
            "manylinux_2_28",
            None,
            "Linux",
            "armv7l",
            False,
            {
                "manylinux_image": "manylinux_2_28_armhf:latest",
                "vendor_base": "almalinux",
                "use_non_root_user": True,
            },
        ),
        # macOS on x86_64
        (
            "manylinux2014",
            None,
            "Darwin",
            "x86_64",
            True,
            {
                "manylinux_image": "manylinux2014_x86_64:latest",
                "vendor_base": "centos",
                "use_non_root_user": False,
            },
        ),
    ],
)
def test_output_format_template_context(
    create_command,
    first_app_config,
    manylinux,
    tag,
    host_os,
    host_arch,
    is_user_mapped,
    context,
):
    """The template context reflects the manylinux name, tag and architecture."""
    # Mock Docker user mapping setting for `use_non_root_user`
    create_command.tools.docker = MagicMock()
    create_command.tools.docker.is_user_mapped = is_user_mapped

    if manylinux:
        first_app_config.manylinux = manylinux
    if tag:
        first_app_config.manylinux_image_tag = tag

    create_command.tools.host_os = host_os
    create_command.tools.host_arch = host_arch

    assert create_command.output_format_template_context(first_app_config) == context


def test_output_format_template_context_bad_tag(create_command, first_app_config):
    """An unknown manylinux tag raises an error."""
    first_app_config.manylinux = "unknown"
    with pytest.raises(BriefcaseConfigError, match=r"Unknown manylinux tag 'unknown'"):
        assert create_command.output_format_template_context(first_app_config)


def test_output_format_no_docker(create_command, first_app_config):
    """If not using Docker, `use_non_root_user` default in template is used."""
    context = create_command.output_format_template_context(first_app_config)

    assert "use_non_root_user" not in context
