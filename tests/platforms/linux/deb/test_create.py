from unittest.mock import Mock

import pytest

from briefcase.exceptions import BriefcaseCommandError, UnsupportedHostError
from briefcase.platforms.linux import deb

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
        match="Linux .deb projects can only be built on Linux, or on macOS using Docker.",
    ):
        create_command()


@pytest.mark.parametrize("host_os", ["Darwin", "Windows", "WeirdOS"])
def test_unsupported_host_os_without_docker(create_command, host_os, tmp_path):
    """Error raised for an unsupported OS when not using Docker."""
    create_command.target_image = None
    create_command.tools.host_os = host_os

    with pytest.raises(
        UnsupportedHostError,
        match="Linux .deb projects can only be built on Linux, or on macOS using Docker.",
    ):
        create_command()


def test_supported_host_os_docker(create_command):
    """If using Docker on a supported host, no error is raised"""
    create_command.target_image = "somevendor:surprising"
    create_command.tools.host_os = "Linux"

    # Verify the host
    create_command.verify_host()


def test_supported_host_os_debian(create_command, monkeypatch):
    """If we're on a Linux, and not using Docker, a check is made for Debian-properties"""
    create_command.target_image = None
    create_command.tools.host_os = "Linux"

    # Mock the existence of the debian_version file.
    debian_version = Mock()
    Path = Mock(return_value=debian_version)
    debian_version.exists.return_value = True
    monkeypatch.setattr(deb, "Path", Path)

    # Verify the host
    create_command.verify_host()

    # The right path was checked
    Path.assert_called_once_with("/etc/debian_version")


def test_supported_host_os_not_debian(create_command, monkeypatch):
    """If we're on a Linux, and not using Docker, and we're *not* on a Debian-alike, raise an error"""
    create_command.target_image = None
    create_command.tools.host_os = "Linux"

    # Mock the existence of the debian_version file.
    debian_version = Mock()
    Path = Mock(return_value=debian_version)
    debian_version.exists.return_value = False
    monkeypatch.setattr(deb, "Path", Path)

    # Verify the host
    with pytest.raises(
        BriefcaseCommandError,
        match=r"Cannot build \.deb packages on a Linux distribution that isn't Debian-based\.",
    ):
        create_command.verify_host()

    # The right path was checked
    Path.assert_called_once_with("/etc/debian_version")


def test_output_format_template_context_no_long_description(
    create_command, first_app_config
):
    "If there's no long description, an error is raised."
    # Add some properties defined in config finalization
    first_app_config.python_version_tag = "3.X"
    first_app_config.target_image = "somevendor:surprising"
    first_app_config.glibc_version = "2.42"

    with pytest.raises(
        BriefcaseCommandError,
        match=r"App configuration does not define `long_description`\. "
        r"Debian packaging guidelines require a long description\.",
    ):
        create_command.output_format_template_context(first_app_config)


def test_output_format_template_context(create_command, first_app_config):
    "The template context contains additional deb-specific properties"
    # Add some properties defined in config finalization
    first_app_config.python_version_tag = "3.X"
    first_app_config.target_image = "somevendor:surprising"
    first_app_config.glibc_version = "2.42"

    # Add a long description
    first_app_config.long_description = "This is a long\ndescription."

    # Generate the context
    context = create_command.output_format_template_context(first_app_config)

    # Deb-specific context
    assert context["python_version"] == "3.X"
    assert context["docker_base_image"] == "somevendor:surprising"
    assert context["system_runtime_requires"] == "libc6 (>=2.42), python3.X"


def test_output_format_template_context_extra_runtime_requires(
    create_command, first_app_config
):
    "If the app defines extra runtime requirements, they're included"
    # Add some properties defined in config finalization
    first_app_config.python_version_tag = "3.X"
    first_app_config.target_image = "somevendor:surprising"
    first_app_config.glibc_version = "2.42"
    # Add extra runtime requirements
    first_app_config.system_runtime_requires = ["first", "second (>=1.23)"]

    # Add a long description
    first_app_config.long_description = "This is a long\ndescription."

    # Generate the context
    context = create_command.output_format_template_context(first_app_config)

    # Deb-specific context
    assert context["python_version"] == "3.X"
    assert context["docker_base_image"] == "somevendor:surprising"
    assert (
        context["system_runtime_requires"]
        == "libc6 (>=2.42), python3.X, first, second (>=1.23)"
    )


def test_install_extra_resources(create_command, first_app_config, capsys, tmp_path):
    "Extra app resources needed by DEB are installed"
    # Specify a system python app for a dummy vendor
    first_app_config.target_vendor = "somevendor"
    first_app_config.target_codename = "surprising"
    first_app_config.python_source = "system"

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
        / "system"
        / "First App"
        / "LICENSE"
    ).exists()
    assert (
        tmp_path
        / "base_path"
        / "linux"
        / "somevendor"
        / "surprising"
        / "system"
        / "First App"
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
    first_app_config.python_source = "system"

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
        / "system"
        / "First App"
        / "LICENSE"
    ).exists()
    assert (
        tmp_path
        / "base_path"
        / "linux"
        / "somevendor"
        / "surprising"
        / "system"
        / "First App"
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
    first_app_config.python_source = "system"

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
        / "system"
        / "First App"
        / "LICENSE"
    ).exists()
    assert not (
        tmp_path
        / "base_path"
        / "linux"
        / "somevendor"
        / "surprising"
        / "system"
        / "First App"
        / "CHANGELOG"
    ).exists()

    # License didn't exist, so warning message was recorded
    output = capsys.readouterr().out
    assert "WARNING: No LICENSE file!" not in output
    assert "WARNING: No CHANGELOG file!" in output
