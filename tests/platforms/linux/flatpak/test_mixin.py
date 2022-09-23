from unittest.mock import MagicMock

import pytest

from briefcase.console import Console, Log
from briefcase.exceptions import BriefcaseCommandError, BriefcaseConfigError
from briefcase.integrations.flatpak import Flatpak
from briefcase.integrations.subprocess import Subprocess
from briefcase.platforms.linux.flatpak import LinuxFlatpakCreateCommand


def test_binary_path(first_app_config, tmp_path):
    """The binary path is the marker file."""
    command = LinuxFlatpakCreateCommand(
        logger=Log(),
        console=Console(),
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )
    binary_path = command.binary_path(first_app_config)

    assert (
        binary_path
        == tmp_path
        / "base_path"
        / "linux"
        / "flatpak"
        / "First App"
        / "com.example.first-app"
    )


def test_distribution_path(first_app_config, tmp_path):
    """The distribution path is a flatpak bundle."""
    command = LinuxFlatpakCreateCommand(
        logger=Log(),
        console=Console(),
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )
    # Force the architecture to something odd for test purposes.
    command.tools.host_arch = "gothic"
    distribution_path = command.distribution_path(first_app_config, "flatpak")

    assert (
        distribution_path
        == tmp_path / "base_path" / "linux" / "First_App-0.0.1-gothic.flatpak"
    )


def test_default_runtime_repo(first_app_config, tmp_path):
    """The flathub repository is the default runtime repository."""
    command = LinuxFlatpakCreateCommand(
        logger=Log(),
        console=Console(),
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )

    assert command.flatpak_runtime_repo(first_app_config) == (
        "flathub",
        "https://flathub.org/repo/flathub.flatpakrepo",
    )


def test_custom_runtime_repo(first_app_config, tmp_path):
    """A custom runtime repo can be specified."""
    first_app_config.flatpak_runtime_repo_alias = "custom_repo"
    first_app_config.flatpak_runtime_repo_url = "https://example.com/flatpak/runtime"

    command = LinuxFlatpakCreateCommand(
        logger=Log(),
        console=Console(),
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )

    assert command.flatpak_runtime_repo(first_app_config) == (
        "custom_repo",
        "https://example.com/flatpak/runtime",
    )


def test_custom_runtime_repo_no_alias(first_app_config, tmp_path):
    """If a custom runtime repo URL is specified, an alias must be specified as
    well."""
    first_app_config.flatpak_runtime_repo_url = "https://example.com/flatpak/runtime"

    command = LinuxFlatpakCreateCommand(
        logger=Log(),
        console=Console(),
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )

    with pytest.raises(
        BriefcaseConfigError,
        match="If you specify a custom Flatpak runtime repository",
    ):
        command.flatpak_runtime_repo(first_app_config)


def test_default_runtime_config(first_app_config, tmp_path):
    """Flatpak apps use a default runtime configuration."""

    command = LinuxFlatpakCreateCommand(
        logger=Log(),
        console=Console(),
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )

    assert command.flatpak_runtime(first_app_config) == "org.freedesktop.Platform"
    assert command.flatpak_runtime_version(first_app_config) == "21.08"
    assert command.flatpak_sdk(first_app_config) == "org.freedesktop.Sdk"


def test_custom_runtime(first_app_config, tmp_path):
    """A custom runtime can be specified."""
    first_app_config.flatpak_runtime = "org.beeware.Platform"
    first_app_config.flatpak_runtime_version = "37.42"
    first_app_config.flatpak_sdk = "org.beeware.SDK"

    command = LinuxFlatpakCreateCommand(
        logger=Log(),
        console=Console(),
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )

    assert command.flatpak_runtime(first_app_config) == "org.beeware.Platform"
    assert command.flatpak_runtime_version(first_app_config) == "37.42"
    assert command.flatpak_sdk(first_app_config) == "org.beeware.SDK"


def test_custom_runtime_runtime_only(first_app_config, tmp_path):
    """If the user only defines a runtime, accessing the SDK raises an
    error."""
    first_app_config.flatpak_runtime = "org.beeware.Platform"
    first_app_config.flatpak_runtime_version = "37.42"

    command = LinuxFlatpakCreateCommand(
        logger=Log(),
        console=Console(),
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )

    with pytest.raises(
        BriefcaseConfigError,
        match=r"If you specify a custom Flatpak runtime, you must also specify a corresponding Flatpak SDK.",
    ):
        command.flatpak_runtime(first_app_config)


def test_custom_runtime_sdk_only(first_app_config, tmp_path):
    """If the user only defines an SDK, accessing the runtime raises an
    error."""
    first_app_config.flatpak_runtime_version = "37.42"
    first_app_config.flatpak_sdk = "org.beeware.SDK"

    command = LinuxFlatpakCreateCommand(
        logger=Log(),
        console=Console(),
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )

    with pytest.raises(
        BriefcaseConfigError,
        match=r"If you specify a custom Flatpak SDK, you must also specify a corresponding Flatpak runtime.",
    ):
        command.flatpak_sdk(first_app_config)


def test_verify_linux(tmp_path):
    """Verifying on Linux creates an SDK wrapper."""
    command = LinuxFlatpakCreateCommand(
        logger=Log(),
        console=Console(),
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )
    command.tools.host_os = "Linux"
    command.tools.subprocess = MagicMock(spec_set=Subprocess)

    # Verify the tools
    command.verify_tools()

    # No error, and an SDK wrapper is created
    assert isinstance(command.tools.flatpak, Flatpak)


def test_verify_non_linux(tmp_path):
    """Verifying on non-Linux raises an error."""
    command = LinuxFlatpakCreateCommand(
        logger=Log(),
        console=Console(),
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )
    command.tools.host_os = "WeirdOS"
    command.tools.subprocess = MagicMock(spec_set=Subprocess)

    # Verify the tools
    with pytest.raises(BriefcaseCommandError):
        command.verify_tools()
