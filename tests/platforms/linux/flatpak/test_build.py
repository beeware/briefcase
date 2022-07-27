from unittest import mock

from briefcase.platforms.linux.flatpak import LinuxFlatpakBuildCommand


def test_build(first_app_config, tmp_path):
    """A flatpak can be built."""
    command = LinuxFlatpakBuildCommand(base_path=tmp_path)
    command.flatpak = mock.MagicMock()

    first_app_config.flatpak_runtime_repo_url = "https://example.com/flatpak/repo"
    first_app_config.flatpak_runtime_repo_alias = "custom-repo"

    first_app_config.flatpak_runtime = "org.beeware.Platform"
    first_app_config.flatpak_runtime_version = "37.42"
    first_app_config.flatpak_sdk = "org.beeware.SDK"

    command.build_app(first_app_config)

    # Repo is verified
    command.flatpak.verify_repo.assert_called_once_with(
        repo_alias="custom-repo",
        url="https://example.com/flatpak/repo",
    )

    # Runtimes are verified
    command.flatpak.verify_runtime.assert_called_once_with(
        repo_alias="custom-repo",
        runtime="org.beeware.Platform",
        runtime_version="37.42",
        sdk="org.beeware.SDK",
    )

    # The build is invoked
    command.flatpak.build.assert_called_once_with(
        bundle="com.example",
        app_name="first-app",
        path=tmp_path / "linux" / "flatpak" / "First App",
    )
