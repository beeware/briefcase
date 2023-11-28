from unittest.mock import MagicMock

import pytest

import briefcase.platforms.linux.flatpak
from briefcase.console import Console, Log
from briefcase.exceptions import BriefcaseConfigError
from briefcase.integrations.flatpak import Flatpak
from briefcase.integrations.subprocess import Subprocess
from briefcase.platforms.linux.flatpak import LinuxFlatpakCreateCommand


@pytest.fixture
def create_command(tmp_path):
    return LinuxFlatpakCreateCommand(
        logger=Log(),
        console=Console(),
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )


def test_binary_path(create_command, first_app_config, tmp_path):
    """The binary path is the marker file."""
    binary_path = create_command.binary_path(first_app_config)

    expected_path = (
        tmp_path
        / "base_path"
        / "build"
        / "first-app"
        / "linux"
        / "flatpak"
        / "com.example.first-app"
    )
    assert binary_path == expected_path


def test_project_path(create_command, first_app_config, tmp_path):
    """The project path is the bundle path."""
    project_path = create_command.project_path(first_app_config)
    bundle_path = create_command.bundle_path(first_app_config)

    expected_path = tmp_path / "base_path/build/first-app/linux/flatpak"
    assert expected_path == project_path == bundle_path


def test_distribution_path(create_command, first_app_config, tmp_path):
    """The distribution path is a flatpak bundle."""
    # Force the architecture to something odd for test purposes.
    create_command.tools.host_arch = "gothic"
    distribution_path = create_command.distribution_path(first_app_config)

    expected_path = tmp_path / "base_path/dist/First_App-0.0.1-gothic.flatpak"
    assert distribution_path == expected_path


def test_default_runtime_repo(create_command, first_app_config):
    """The flathub repository is the default runtime repository."""
    expected_repo = ("flathub", "https://flathub.org/repo/flathub.flatpakrepo")
    assert create_command.flatpak_runtime_repo(first_app_config) == expected_repo


def test_custom_runtime_repo(create_command, first_app_config):
    """A custom runtime repo can be specified."""
    first_app_config.flatpak_runtime_repo_alias = "custom_repo"
    first_app_config.flatpak_runtime_repo_url = "https://example.com/flatpak/runtime"

    expected_repo = ("custom_repo", "https://example.com/flatpak/runtime")
    assert create_command.flatpak_runtime_repo(first_app_config) == expected_repo


def test_custom_runtime_repo_no_alias(create_command, first_app_config):
    """If a custom runtime repo URL is specified, an alias must be specified as well."""
    first_app_config.flatpak_runtime_repo_url = "https://example.com/flatpak/runtime"

    with pytest.raises(
        BriefcaseConfigError,
        match="If you specify a custom Flatpak runtime repository",
    ):
        create_command.flatpak_runtime_repo(first_app_config)


def test_custom_runtime(create_command, first_app_config):
    """A custom runtime can be specified."""
    first_app_config.flatpak_runtime = "org.beeware.Platform"
    first_app_config.flatpak_runtime_version = "37.42"
    first_app_config.flatpak_sdk = "org.beeware.SDK"

    assert create_command.flatpak_runtime(first_app_config) == "org.beeware.Platform"
    assert create_command.flatpak_runtime_version(first_app_config) == "37.42"
    assert create_command.flatpak_sdk(first_app_config) == "org.beeware.SDK"


def test_missing_runtime(create_command, first_app_config):
    """Error if App config is missing the runtime."""
    first_app_config.flatpak_runtime_version = "37.42"
    first_app_config.flatpak_sdk = "org.beeware.SDK"

    with pytest.raises(
        BriefcaseConfigError,
        match="Briefcase configuration error: The App does not specify the Flatpak runtime to use",
    ):
        create_command.flatpak_runtime(first_app_config)


def test_missing_sdk(create_command, first_app_config):
    """Error if App config is missing the SDK."""
    first_app_config.flatpak_runtime = "org.beeware.Platform"
    first_app_config.flatpak_runtime_version = "37.42"

    with pytest.raises(
        BriefcaseConfigError,
        match="Briefcase configuration error: The App does not specify the Flatpak SDK to use",
    ):
        create_command.flatpak_sdk(first_app_config)


def test_missing_runtime_version(create_command, first_app_config):
    """Error if App config is missing the runtime version."""
    first_app_config.flatpak_runtime = "org.beeware.Platform"
    first_app_config.flatpak_sdk = "org.beeware.SDK"

    with pytest.raises(
        BriefcaseConfigError,
        match="Briefcase configuration error: The App does not specify the version of the Flatpak runtime to use",
    ):
        create_command.flatpak_runtime_version(first_app_config)


def test_verify_linux(create_command, monkeypatch, tmp_path):
    """Verifying on Linux creates an SDK wrapper."""
    create_command.tools.host_os = "Linux"
    create_command.tools.subprocess = MagicMock(spec_set=Subprocess)

    mock_flatpak_verify = MagicMock(wraps=Flatpak.verify)
    monkeypatch.setattr(
        briefcase.platforms.linux.flatpak.Flatpak,
        "verify",
        mock_flatpak_verify,
    )

    # Verify the tools
    create_command.verify_tools()

    # Flatpak tool was verified
    mock_flatpak_verify.assert_called_once_with(tools=create_command.tools)
    assert isinstance(create_command.tools.flatpak, Flatpak)
