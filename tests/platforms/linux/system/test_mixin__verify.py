from unittest.mock import MagicMock

from briefcase.integrations.docker import Docker, DockerAppContext
from briefcase.integrations.subprocess import Subprocess


def test_linux_no_docker(monkeypatch, create_command, first_app_config):
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


def test_linux_docker(create_command, tmp_path, first_app_config, monkeypatch):
    """If Docker is enabled on Linux, the Docker alias is set."""
    create_command.tools.host_os = "Linux"
    create_command.target_image = "somevendor:surprising"

    # Force a dummy vendor:codename for test purposes.
    first_app_config.target_vendor = "somevendor"
    first_app_config.target_codename = "surprising"
    first_app_config.target_vendor_base = "basevendor"
    first_app_config.python_version_tag = "3"

    # Mock Docker tool verification
    Docker.verify = MagicMock()
    DockerAppContext.verify = MagicMock()
    create_command.verify_python = MagicMock()

    # Verify the tools
    create_command.verify_tools()
    create_command.verify_app_tools(app=first_app_config)

    # Docker and Docker app context are verified
    Docker.verify.assert_called_with(tools=create_command.tools)
    DockerAppContext.verify.assert_called_with(
        tools=create_command.tools,
        app=first_app_config,
        image_tag="briefcase/com.example.first-app:somevendor-surprising",
        dockerfile_path=tmp_path
        / "base_path"
        / "build"
        / "first-app"
        / "somevendor"
        / "surprising"
        / "Dockerfile",
        app_base_path=tmp_path / "base_path",
        host_bundle_path=tmp_path
        / "base_path"
        / "build"
        / "first-app"
        / "somevendor"
        / "surprising",
        host_data_path=tmp_path / "briefcase",
        python_version="3",
    )

    # Python was also verified
    create_command.verify_python.assert_called_once_with(first_app_config)

    # Reset the mock, then invoke verify_app_tools a second time.
    create_command.verify_python.reset_mock()
    create_command.verify_app_tools(app=first_app_config)

    # Python will *not* be verified a second time.
    create_command.verify_python.assert_not_called()


def test_non_linux_docker(create_command, tmp_path, first_app_config):
    """If Docker is enabled on non-Linux, the Docker alias is set."""
    create_command.tools.host_os = "Darwin"
    create_command.target_image = "somevendor:surprising"

    # Force a dummy vendor:codename for test purposes.
    first_app_config.target_vendor = "somevendor"
    first_app_config.target_codename = "surprising"
    first_app_config.target_vendor_base = "basevendor"
    first_app_config.python_version_tag = "3"

    # Mock Docker tool verification
    Docker.verify = MagicMock()
    DockerAppContext.verify = MagicMock()
    create_command.verify_python = MagicMock()

    # Verify the tools
    create_command.verify_tools()
    create_command.verify_app_tools(app=first_app_config)

    # Docker and Docker app context are verified
    Docker.verify.assert_called_with(tools=create_command.tools)
    DockerAppContext.verify.assert_called_with(
        tools=create_command.tools,
        app=first_app_config,
        image_tag="briefcase/com.example.first-app:somevendor-surprising",
        dockerfile_path=tmp_path
        / "base_path"
        / "build"
        / "first-app"
        / "somevendor"
        / "surprising"
        / "Dockerfile",
        app_base_path=tmp_path / "base_path",
        host_bundle_path=tmp_path
        / "base_path"
        / "build"
        / "first-app"
        / "somevendor"
        / "surprising",
        host_data_path=tmp_path / "briefcase",
        python_version="3",
    )

    # Python was also verified
    create_command.verify_python.assert_called_once_with(first_app_config)

    # Reset the mock, then invoke verify_app_tools a second time.
    create_command.verify_python.reset_mock()
    create_command.verify_app_tools(app=first_app_config)

    # Python will *not* be verified a second time.
    create_command.verify_python.assert_not_called()
