from unittest import mock

from briefcase.console import Console, Log
from briefcase.integrations.flatpak import Flatpak
from briefcase.platforms.linux.flatpak import LinuxFlatpakBuildCommand


def test_build(first_app_config, tmp_path):
    """A flatpak can be built."""
    command = LinuxFlatpakBuildCommand(
        logger=Log(),
        console=Console(),
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )
    command.tools.flatpak = mock.MagicMock(spec_set=Flatpak)

    first_app_config.flatpak_runtime_repo_url = "https://example.com/flatpak/repo"
    first_app_config.flatpak_runtime_repo_alias = "custom-repo"

    first_app_config.flatpak_runtime = "org.beeware.Platform"
    first_app_config.flatpak_runtime_version = "37.42"
    first_app_config.flatpak_sdk = "org.beeware.SDK"

    command.build_app(first_app_config)

    # Repo is verified
    command.tools.flatpak.verify_repo.assert_called_once_with(
        repo_alias="custom-repo",
        url="https://example.com/flatpak/repo",
    )

    # Runtimes are verified
    command.tools.flatpak.verify_runtime.assert_called_once_with(
        repo_alias="custom-repo",
        runtime="org.beeware.Platform",
        runtime_version="37.42",
        sdk="org.beeware.SDK",
    )

    # The build is invoked
    command.tools.flatpak.build.assert_called_once_with(
        bundle="com.example",
        app_name="first-app",
        path=tmp_path / "base_path" / "linux" / "flatpak" / "First App",
    )
