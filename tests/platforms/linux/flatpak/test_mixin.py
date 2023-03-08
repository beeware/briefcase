from unittest.mock import MagicMock

import pytest

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


def test_distribution_path(create_command, first_app_config, tmp_path):
    """The distribution path is a flatpak bundle."""
    # Force the architecture to something odd for test purposes.
    create_command.tools.host_arch = "gothic"
    distribution_path = create_command.distribution_path(first_app_config)

    expected_path = tmp_path / "base_path" / "dist" / "First_App-0.0.1-gothic.flatpak"
    assert distribution_path == expected_path


def test_default_runtime_repo(create_command, first_app_config, tmp_path):
    """The flathub repository is the default runtime repository."""
    expected_repo = ("flathub", "https://flathub.org/repo/flathub.flatpakrepo")
    assert create_command.flatpak_runtime_repo(first_app_config) == expected_repo


def test_custom_runtime_repo(create_command, first_app_config, tmp_path):
    """A custom runtime repo can be specified."""
    first_app_config.flatpak_runtime_repo_alias = "custom_repo"
    first_app_config.flatpak_runtime_repo_url = "https://example.com/flatpak/runtime"

    expected_repo = ("custom_repo", "https://example.com/flatpak/runtime")
    assert create_command.flatpak_runtime_repo(first_app_config) == expected_repo


def test_custom_runtime_repo_no_alias(create_command, first_app_config, tmp_path):
    """If a custom runtime repo URL is specified, an alias must be specified as well."""
    first_app_config.flatpak_runtime_repo_url = "https://example.com/flatpak/runtime"

    with pytest.raises(
        BriefcaseConfigError,
        match="If you specify a custom Flatpak runtime repository",
    ):
        create_command.flatpak_runtime_repo(first_app_config)


def test_default_runtime_config(create_command, first_app_config, tmp_path):
    """Flatpak apps use a default runtime configuration."""

    assert (
        create_command.flatpak_runtime(first_app_config) == "org.freedesktop.Platform"
    )
    assert create_command.flatpak_runtime_version(first_app_config) == "21.08"
    assert create_command.flatpak_sdk(first_app_config) == "org.freedesktop.Sdk"


def test_custom_runtime(create_command, first_app_config, tmp_path):
    """A custom runtime can be specified."""
    first_app_config.flatpak_runtime = "org.beeware.Platform"
    first_app_config.flatpak_runtime_version = "37.42"
    first_app_config.flatpak_sdk = "org.beeware.SDK"

    assert create_command.flatpak_runtime(first_app_config) == "org.beeware.Platform"
    assert create_command.flatpak_runtime_version(first_app_config) == "37.42"
    assert create_command.flatpak_sdk(first_app_config) == "org.beeware.SDK"


def test_custom_runtime_runtime_only(create_command, first_app_config, tmp_path):
    """If the user only defines a runtime, accessing the SDK raises an error."""
    first_app_config.flatpak_runtime = "org.beeware.Platform"
    first_app_config.flatpak_runtime_version = "37.42"

    with pytest.raises(
        BriefcaseConfigError,
        match=r"If you specify a custom Flatpak runtime, you must also specify a corresponding Flatpak SDK.",
    ):
        create_command.flatpak_runtime(first_app_config)


def test_custom_runtime_sdk_only(create_command, first_app_config, tmp_path):
    """If the user only defines an SDK, accessing the runtime raises an error."""
    first_app_config.flatpak_runtime_version = "37.42"
    first_app_config.flatpak_sdk = "org.beeware.SDK"

    with pytest.raises(
        BriefcaseConfigError,
        match=r"If you specify a custom Flatpak SDK, you must also specify a corresponding Flatpak runtime.",
    ):
        create_command.flatpak_sdk(first_app_config)


def test_verify_linux(create_command, tmp_path):
    """Verifying on Linux creates an SDK wrapper."""
    create_command.tools.host_os = "Linux"
    create_command.tools.subprocess = MagicMock(spec_set=Subprocess)

    # Verify the tools
    create_command.verify_tools()

    # No error and an SDK wrapper is created
    assert isinstance(create_command.tools.flatpak, Flatpak)
