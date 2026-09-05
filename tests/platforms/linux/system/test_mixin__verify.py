from unittest.mock import MagicMock

import pytest

import briefcase.platforms.linux.system
from briefcase.integrations.docker import Docker, DockerAppContext
from briefcase.integrations.subprocess import Subprocess


def test_linux_no_docker(create_command, first_app_config, monkeypatch):
    """If Docker is disabled on Linux, the app_context is Subprocess."""
    create_command.tools.host_os = "Linux"
    create_command.target_image = None

    # Force a dummy vendor:codename for test purposes.
    first_app_config.target_vendor = "somevendor"
    first_app_config.target_codename = "surprising"
    first_app_config.target_vendor_base = "basevendor"

    # Mock the existence of a valid non-docker system Python
    create_command.verify_system_python = MagicMock()

    # Verify the tools
    create_command.verify_tools()
    create_command.verify_app_tools(app=first_app_config)

    # No error and Subprocess is used.
    assert isinstance(create_command.tools[first_app_config].app_context, Subprocess)
    # Docker is not verified.
    assert not hasattr(create_command.tools, "docker")
    # System python is verified
    create_command.verify_system_python.assert_called_once_with()

    # Reset the mock, then invoke verify_app_tools a second time.
    create_command.verify_system_python.reset_mock()
    create_command.verify_app_tools(app=first_app_config)

    # Python will *not* be verified a second time.
    create_command.verify_system_python.assert_not_called()


def test_linux_docker(create_command, first_app_config, tmp_path, monkeypatch):
    """If Docker is enabled on Linux, the Docker alias is set."""
    create_command.tools.host_os = "Linux"
    create_command.target_image = "somevendor:surprising"
    create_command.extra_docker_build_args = ["--option-one", "--option-two"]

    # Force a dummy vendor:codename for test purposes.
    first_app_config.target_vendor = "somevendor"
    first_app_config.target_codename = "surprising"
    first_app_config.target_vendor_base = "basevendor"
    first_app_config.python_version_tag = "3"

    # Mock Docker tool verification
    mock__version_compat = MagicMock(spec=Docker._version_compat)
    mock__user_access = MagicMock(spec=Docker._user_access)
    mock__buildx_installed = MagicMock(spec=Docker._buildx_installed)
    mock__is_user_mapping_enabled = MagicMock(spec=Docker._is_user_mapping_enabled)
    monkeypatch.setattr(
        briefcase.platforms.linux.system.Docker,
        "_version_compat",
        mock__version_compat,
    )
    monkeypatch.setattr(
        briefcase.platforms.linux.system.Docker,
        "_user_access",
        mock__user_access,
    )
    monkeypatch.setattr(
        briefcase.platforms.linux.system.Docker,
        "_buildx_installed",
        mock__buildx_installed,
    )
    monkeypatch.setattr(
        briefcase.platforms.linux.system.Docker,
        "_is_user_mapping_enabled",
        mock__is_user_mapping_enabled,
    )
    mock_docker_app_context_verify = MagicMock(spec=DockerAppContext.verify)
    monkeypatch.setattr(
        briefcase.platforms.linux.system.DockerAppContext,
        "verify",
        mock_docker_app_context_verify,
    )
    create_command.verify_docker_python = MagicMock()

    # Verify the tools
    create_command.verify_tools()
    create_command.verify_app_tools(app=first_app_config)

    # Docker and Docker app context are verified
    mock__version_compat.assert_called_with(tools=create_command.tools)
    mock__user_access.assert_called_with(tools=create_command.tools)
    mock__buildx_installed.assert_called_with(tools=create_command.tools)
    mock__is_user_mapping_enabled.assert_called_with("somevendor:surprising")
    assert isinstance(create_command.tools.docker, Docker)
    mock_docker_app_context_verify.assert_called_with(
        tools=create_command.tools,
        app=first_app_config,
        image_tag="briefcase/com.example.first-app:somevendor-surprising",
        dockerfile_path=tmp_path
        / "base_path/build/first-app/somevendor/surprising/Dockerfile",
        app_base_path=tmp_path / "base_path",
        host_bundle_path=tmp_path / "base_path/build/first-app/somevendor/surprising",
        host_data_path=tmp_path / "briefcase",
        python_version="3",
        extra_build_args=["--option-one", "--option-two"],
    )

    # Python was also verified
    create_command.verify_docker_python.assert_called_once_with(first_app_config)

    # Reset the mock, then invoke verify_app_tools a second time.
    create_command.verify_docker_python.reset_mock()
    create_command.verify_app_tools(app=first_app_config)

    # Python will *not* be verified a second time.
    create_command.verify_docker_python.assert_not_called()


@pytest.mark.parametrize(
    ("vendor_base", "packaging_format", "expected_requires"),
    [
        # The signing tool is added to the image requirements for a known format
        ("debian", "deb", ["debsigs"]),
        ("rhel", "rpm", ["rpm-sign"]),
        ("arch", "pkg", ["gnupg"]),
        # On SUSE, rpmsign is provided by rpm-build; there is no `rpm-sign`
        # package
        ("suse", "rpm", ["rpm-build"]),
        # An unresolved "system" packaging format has no signing tool; format
        # resolution happens during app config finalization.
        ("basevendor", "system", []),
    ],
)
def test_linux_docker_adds_signing_tool(
    create_command,
    first_app_config,
    tmp_path,
    monkeypatch,
    vendor_base,
    packaging_format,
    expected_requires,
):
    """If Docker is enabled on Linux, the signing tool is added to the image
    requirements.

    This must happen during any command's app tool verification, because the Docker
    image is built before the signing identity is selected; if the signing tool isn't in
    the image, signing a package built with Docker will fail.
    """
    create_command.tools.host_os = "Linux"
    create_command.target_image = "somevendor:surprising"
    create_command.extra_docker_build_args = []

    # Force a dummy vendor:codename for test purposes.
    first_app_config.target_vendor = "somevendor"
    first_app_config.target_codename = "surprising"
    first_app_config.target_vendor_base = vendor_base
    first_app_config.packaging_format = packaging_format
    first_app_config.python_version_tag = "3"

    # Mock Docker tool verification
    mock__version_compat = MagicMock(spec=Docker._version_compat)
    mock__user_access = MagicMock(spec=Docker._user_access)
    mock__buildx_installed = MagicMock(spec=Docker._buildx_installed)
    mock__is_user_mapping_enabled = MagicMock(spec=Docker._is_user_mapping_enabled)
    monkeypatch.setattr(
        briefcase.platforms.linux.system.Docker,
        "_version_compat",
        mock__version_compat,
    )
    monkeypatch.setattr(
        briefcase.platforms.linux.system.Docker,
        "_user_access",
        mock__user_access,
    )
    monkeypatch.setattr(
        briefcase.platforms.linux.system.Docker,
        "_buildx_installed",
        mock__buildx_installed,
    )
    monkeypatch.setattr(
        briefcase.platforms.linux.system.Docker,
        "_is_user_mapping_enabled",
        mock__is_user_mapping_enabled,
    )
    mock_docker_app_context_verify = MagicMock(spec=DockerAppContext.verify)
    monkeypatch.setattr(
        briefcase.platforms.linux.system.DockerAppContext,
        "verify",
        mock_docker_app_context_verify,
    )
    create_command.verify_docker_python = MagicMock()

    # Verify the tools
    create_command.verify_tools()
    create_command.verify_app_tools(app=first_app_config)

    # The signing tool has been added to the image requirements
    assert getattr(first_app_config, "system_requires", None) == expected_requires


def test_non_linux_docker(create_command, first_app_config, tmp_path, monkeypatch):
    """If Docker is enabled on non-Linux, the Docker alias is set."""
    create_command.tools.host_os = "Darwin"
    create_command.target_image = "somevendor:surprising"
    create_command.extra_docker_build_args = ["--option-one", "--option-two"]

    # Force a dummy vendor:codename for test purposes.
    first_app_config.target_vendor = "somevendor"
    first_app_config.target_codename = "surprising"
    first_app_config.target_vendor_base = "basevendor"
    first_app_config.python_version_tag = "3"

    # Mock Docker tool verification
    mock__version_compat = MagicMock(spec=Docker._version_compat)
    mock__user_access = MagicMock(spec=Docker._user_access)
    mock__buildx_installed = MagicMock(spec=Docker._buildx_installed)
    mock__is_user_mapping_enabled = MagicMock(spec=Docker._is_user_mapping_enabled)
    monkeypatch.setattr(
        briefcase.platforms.linux.system.Docker,
        "_version_compat",
        mock__version_compat,
    )
    monkeypatch.setattr(
        briefcase.platforms.linux.system.Docker,
        "_user_access",
        mock__user_access,
    )
    monkeypatch.setattr(
        briefcase.platforms.linux.system.Docker,
        "_buildx_installed",
        mock__buildx_installed,
    )
    monkeypatch.setattr(
        briefcase.platforms.linux.system.Docker,
        "_is_user_mapping_enabled",
        mock__is_user_mapping_enabled,
    )
    mock_docker_app_context_verify = MagicMock(spec=DockerAppContext.verify)
    monkeypatch.setattr(
        briefcase.platforms.linux.system.DockerAppContext,
        "verify",
        mock_docker_app_context_verify,
    )
    create_command.verify_docker_python = MagicMock()

    # Verify the tools
    create_command.verify_tools()
    create_command.verify_app_tools(app=first_app_config)

    # Docker and Docker app context are verified
    mock__version_compat.assert_called_with(tools=create_command.tools)
    mock__user_access.assert_called_with(tools=create_command.tools)
    mock__buildx_installed.assert_called_with(tools=create_command.tools)
    mock__is_user_mapping_enabled.assert_called_with("somevendor:surprising")
    assert isinstance(create_command.tools.docker, Docker)
    mock_docker_app_context_verify.assert_called_with(
        tools=create_command.tools,
        app=first_app_config,
        image_tag="briefcase/com.example.first-app:somevendor-surprising",
        dockerfile_path=tmp_path
        / "base_path/build/first-app/somevendor/surprising/Dockerfile",
        app_base_path=tmp_path / "base_path",
        host_bundle_path=tmp_path / "base_path/build/first-app/somevendor/surprising",
        host_data_path=tmp_path / "briefcase",
        python_version="3",
        extra_build_args=["--option-one", "--option-two"],
    )

    # Python was also verified
    create_command.verify_docker_python.assert_called_once_with(first_app_config)

    # Reset the mock, then invoke verify_app_tools a second time.
    create_command.verify_docker_python.reset_mock()
    create_command.verify_app_tools(app=first_app_config)

    # Python will *not* be verified a second time.
    create_command.verify_docker_python.assert_not_called()
