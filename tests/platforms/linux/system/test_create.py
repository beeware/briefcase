import pytest

from briefcase.exceptions import UnsupportedHostError

from ....utils import create_file


def test_default_options(create_command):
    """The default options are as expected."""
    options = create_command.parse_options([])

    assert options == {}

    assert create_command.target_image is None


def test_options(create_command):
    """The extra options can be parsed."""
    options = create_command.parse_options(["--target", "somevendor:surprising"])

    assert options == {}

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
    """If using Docker on a supported host, no error is raised"""
    create_command.target_image = "somevendor:surprising"
    create_command.tools.host_os = "Linux"

    # Verify the host
    create_command.verify_host()


def test_supported_host_os_without_docker(create_command):
    """If not using Docker on a supported host, no error is raised"""
    create_command.target_image = None
    create_command.tools.host_os = "Linux"

    # Verify the host
    create_command.verify_host()


def test_output_format_template_context(create_command, first_app_config):
    "The template context contains additional deb-specific properties"
    # Add some properties defined in config finalization
    first_app_config.python_version_tag = "3.X"
    first_app_config.target_image = "somevendor:surprising"
    first_app_config.target_vendor_base = "basevendor"
    first_app_config.glibc_version = "2.42"

    # Add a long description
    first_app_config.long_description = "This is a long\ndescription."

    # Generate the context
    context = create_command.output_format_template_context(first_app_config)

    # Deb-specific context
    assert context["python_version"] == "3.X"
    assert context["docker_base_image"] == "somevendor:surprising"
    assert context["vendor_base"] == "basevendor"


def test_install_extra_resources(create_command, first_app_config, capsys, tmp_path):
    "Extra app resources needed by DEB are installed"
    # Specify a system python app for a dummy vendor
    first_app_config.target_vendor = "somevendor"
    first_app_config.target_codename = "surprising"

    # Create an empty path index
    create_command._path_index = {first_app_config: {}}

    # Create a dummy LICENSE file
    create_file(tmp_path / "base_path" / "LICENSE", "License file")
    # Create a dummy CHANGELOG file
    create_file(tmp_path / "base_path" / "CHANGELOG", "Change log")

    # Dummy Rolling out the base template (creating the directories)
    create_command.project_path(first_app_config).mkdir(parents=True, exist_ok=True)

    # Install app resources
    create_command.install_app_resources(first_app_config)

    # The two resources files have been created
    assert (
        tmp_path
        / "base_path"
        / "linux"
        / "somevendor"
        / "surprising"
        / "first-app"
        / "LICENSE"
    ).exists()
    assert (
        tmp_path
        / "base_path"
        / "linux"
        / "somevendor"
        / "surprising"
        / "first-app"
        / "CHANGELOG"
    ).exists()

    # No warning messages were recorded
    output = capsys.readouterr().out
    assert "WARNING: No LICENSE file!" not in output
    assert "WARNING: No CHANGELOG file!" not in output


def test_install_extra_resources_missing_license(
    create_command, first_app_config, capsys, tmp_path
):
    """If a license file is missing, a warning is recorded"""
    # Specify a system python app for a dummy vendor
    first_app_config.target_vendor = "somevendor"
    first_app_config.target_codename = "surprising"

    # Create an empty path index
    create_command._path_index = {first_app_config: {}}

    # Create a dummy CHANGELOG file
    create_file(tmp_path / "base_path" / "CHANGELOG", "Change log")

    # Dummy Rolling out the base template (creating the directories)
    create_command.project_path(first_app_config).mkdir(parents=True, exist_ok=True)

    # Install app resources
    create_command.install_app_resources(first_app_config)

    # The changelog was created, license was not.
    assert not (
        tmp_path
        / "base_path"
        / "linux"
        / "somevendor"
        / "surprising"
        / "first-app"
        / "LICENSE"
    ).exists()
    assert (
        tmp_path
        / "base_path"
        / "linux"
        / "somevendor"
        / "surprising"
        / "first-app"
        / "CHANGELOG"
    ).exists()

    # License didn't exist, so warning message was recorded
    output = capsys.readouterr().out
    assert "WARNING: No LICENSE file!" in output
    assert "WARNING: No CHANGELOG file!" not in output


def test_install_extra_resources_missing_changelog(
    create_command, first_app_config, capsys, tmp_path
):
    """If a changelog file is missing, a warning is recorded"""
    # Specify a system python app for a dummy vendor
    first_app_config.target_vendor = "somevendor"
    first_app_config.target_codename = "surprising"

    # Create an empty path index
    create_command._path_index = {first_app_config: {}}

    # Create a dummy LICENSE file
    create_file(tmp_path / "base_path" / "LICENSE", "License file")

    # Dummy Rolling out the base template (creating the directories)
    create_command.project_path(first_app_config).mkdir(parents=True, exist_ok=True)

    # Install app resources
    create_command.install_app_resources(first_app_config)

    # The license was created, changelog was not.
    assert (
        tmp_path
        / "base_path"
        / "linux"
        / "somevendor"
        / "surprising"
        / "first-app"
        / "LICENSE"
    ).exists()
    assert not (
        tmp_path
        / "base_path"
        / "linux"
        / "somevendor"
        / "surprising"
        / "first-app"
        / "CHANGELOG"
    ).exists()

    # License didn't exist, so warning message was recorded
    output = capsys.readouterr().out
    assert "WARNING: No LICENSE file!" not in output
    assert "WARNING: No CHANGELOG file!" in output
