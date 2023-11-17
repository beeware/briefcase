from unittest.mock import MagicMock

import pytest

from briefcase.exceptions import UnsupportedHostError


def test_default_options(create_command):
    """The default options are as expected."""
    options, overrides = create_command.parse_options([])

    assert options == {}
    assert overrides == {}

    assert create_command.target_image is None


def test_options(create_command):
    """The extra options can be parsed."""
    options, overrides = create_command.parse_options(
        ["--target", "somevendor:surprising"]
    )

    assert options == {}
    assert overrides == {}

    assert create_command.target_image == "somevendor:surprising"


@pytest.mark.parametrize("host_os", ["Windows", "WeirdOS"])
def test_unsupported_host_os_with_docker(create_command, host_os, tmp_path):
    """Error raised for an unsupported OS when using Docker."""
    create_command.target_image = "somevendor:surprising"
    create_command.tools.host_os = host_os

    with pytest.raises(
        UnsupportedHostError,
        match="Linux system projects can only be built on Linux, or on macOS using Docker.",
    ):
        create_command()


@pytest.mark.parametrize("host_os", ["Darwin", "Windows", "WeirdOS"])
def test_unsupported_host_os_without_docker(create_command, host_os, tmp_path):
    """Error raised for an unsupported OS when not using Docker."""
    create_command.target_image = None
    create_command.tools.host_os = host_os

    with pytest.raises(
        UnsupportedHostError,
        match="Linux system projects can only be built on Linux, or on macOS using Docker.",
    ):
        create_command()


def test_supported_host_os_docker(create_command):
    """If using Docker on a supported host, no error is raised."""
    create_command.target_image = "somevendor:surprising"
    create_command.tools.host_os = "Linux"

    # Verify the host
    create_command.verify_host()


def test_supported_host_os_without_docker(create_command):
    """If not using Docker on a supported host, no error is raised."""
    create_command.target_image = None
    create_command.tools.host_os = "Linux"

    # Verify the host
    create_command.verify_host()


@pytest.mark.parametrize(
    "is_user_mapped, host_os, use_non_root",
    [
        (False, "Darwin", True),
        (True, "Darwin", True),
        (False, "Linux", True),
        (True, "Linux", False),
    ],
)
def test_output_format_template_context(
    create_command,
    first_app_config,
    is_user_mapped,
    host_os,
    use_non_root,
):
    """The template context contains additional deb-specific properties."""
    # Add some properties defined in config finalization
    first_app_config.python_version_tag = "3.X"
    first_app_config.target_image = "somevendor:surprising"
    first_app_config.target_vendor = "somevendor"
    first_app_config.target_codename = "surprising"
    first_app_config.target_vendor_base = "basevendor"
    first_app_config.glibc_version = "2.42"

    # Mock the host OS
    create_command.tools.host_os = host_os

    # Mock a target Docker image
    create_command.target_image = "somearch:surprising"

    # Mock Docker user mapping setting for `use_non_root_user`
    create_command.tools.docker = MagicMock()
    create_command.tools.docker.is_user_mapped = is_user_mapped

    # Add a long description
    first_app_config.long_description = "This is a long\ndescription."

    # Generate the context
    context = create_command.output_format_template_context(first_app_config)

    # Context extras are what we expect
    assert context == {
        "format": "surprising",
        "python_version": "3.X",
        "docker_base_image": "somevendor:surprising",
        "vendor_base": "basevendor",
        "use_non_root_user": use_non_root,
    }


def test_output_format_template_context_no_docker(create_command, first_app_config):
    """If not using Docker, `use_non_root_user` default in template is used."""
    # Mock the host to Linux to avoid flagging any "always use non-root user on macOS" logic.
    create_command.tools.host_os = "Linux"

    # Add some properties defined in config finalization
    first_app_config.python_version_tag = "3.X"
    first_app_config.target_image = "somevendor:surprising"
    first_app_config.target_vendor = "somevendor"
    first_app_config.target_codename = "surprising"
    first_app_config.target_vendor_base = "basevendor"
    first_app_config.glibc_version = "2.42"

    context = create_command.output_format_template_context(first_app_config)

    # Context extras does not contain `use_non_root_user`
    assert context == {
        "format": "surprising",
        "python_version": "3.X",
        "docker_base_image": "somevendor:surprising",
        "vendor_base": "basevendor",
    }
