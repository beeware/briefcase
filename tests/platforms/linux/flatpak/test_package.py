from unittest import mock

import pytest

from briefcase.console import Console, Log
from briefcase.integrations.flatpak import Flatpak
from briefcase.platforms.linux.flatpak import LinuxFlatpakPackageCommand


@pytest.fixture
def package_command(tmp_path):
    return LinuxFlatpakPackageCommand(
        logger=Log(),
        console=Console(),
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )


def test_package(package_command, first_app_config, tmp_path):
    """A flatpak can be packaged."""
    package_command.tools.flatpak = mock.MagicMock(spec_set=Flatpak)
    # Mock the architecture so that the output filename is consistent
    package_command.tools.host_arch = "gothic"

    first_app_config.flatpak_runtime_repo_url = "https://example.com/flatpak/repo"
    first_app_config.flatpak_runtime_repo_alias = "custom-repo"

    package_command.package_app(first_app_config)

    # A flatpak bundle is created
    package_command.tools.flatpak.bundle.assert_called_once_with(
        repo_url="https://example.com/flatpak/repo",
        bundle_identifier="com.example.first-app",
        app_name="first-app",
        version="0.0.1",
        build_path=tmp_path / "base_path/build/first-app/linux/flatpak",
        output_path=tmp_path / "base_path/dist/First_App-0.0.1-gothic.flatpak",
    )
