from unittest import mock

from briefcase.platforms.linux.flatpak import LinuxFlatpakPackageCommand


def test_package(first_app_config, tmp_path):
    """A flatpak can be packaged."""
    command = LinuxFlatpakPackageCommand(base_path=tmp_path)
    command.flatpak = mock.MagicMock()
    # Mock the architecture so that the output filename is consistent
    command.host_arch = "gothic"

    first_app_config.flatpak_runtime_repo_url = "https://example.com/flatpak/repo"
    first_app_config.flatpak_runtime_repo_alias = "custom-repo"

    command.package_app(first_app_config)

    # A flatpak bundle is created
    command.flatpak.bundle.assert_called_once_with(
        repo_url="https://example.com/flatpak/repo",
        bundle="com.example",
        app_name="first-app",
        version="0.0.1",
        build_path=tmp_path / "linux" / "flatpak" / "First App",
        output_path=tmp_path / "linux" / "First_App-0.0.1-gothic.flatpak",
    )
