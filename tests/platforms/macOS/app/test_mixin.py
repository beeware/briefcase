import pytest

from briefcase.console import Console, Log
from briefcase.exceptions import UnsupportedHostError
from briefcase.platforms.macOS.app import macOSAppCreateCommand, macOSAppPackageCommand


@pytest.fixture
def create_command(tmp_path):
    return macOSAppCreateCommand(
        logger=Log(),
        console=Console(),
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )


@pytest.fixture
def package_command(tmp_path):
    return macOSAppPackageCommand(
        logger=Log(),
        console=Console(),
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )


@pytest.mark.parametrize("host_os", ["Linux", "Windows", "WeirdOS"])
def test_unsupported_host_os(create_command, host_os):
    """Error raised for an unsupported OS."""
    create_command.tools.host_os = host_os

    with pytest.raises(
        UnsupportedHostError,
        match="macOS applications can only be built on macOS.",
    ):
        create_command()


def test_binary_path(create_command, first_app_config, tmp_path):
    binary_path = create_command.binary_path(first_app_config)

    expected_path = (
        tmp_path
        / "base_path"
        / "build"
        / "first-app"
        / "macos"
        / "app"
        / "First App.app"
    )
    assert binary_path == expected_path


def test_project_path(create_command, first_app_config, tmp_path):
    """The project path is the Contents directory."""
    project_path = create_command.project_path(first_app_config)

    expected_path = (
        tmp_path
        / "base_path"
        / "build"
        / "first-app"
        / "macos"
        / "app"
        / "First App.app"
        / "Contents"
    )
    assert expected_path == project_path


def test_distribution_path_app(package_command, first_app_config, tmp_path):
    first_app_config.packaging_format = "app"
    distribution_path = package_command.distribution_path(first_app_config)

    expected_path = tmp_path / "base_path/dist/First App-0.0.1.app.zip"
    assert distribution_path == expected_path


def test_distribution_path_dmg(package_command, first_app_config, tmp_path):
    first_app_config.packaging_format = "dmg"
    distribution_path = package_command.distribution_path(first_app_config)

    expected_path = tmp_path / "base_path/dist/First App-0.0.1.dmg"
    assert distribution_path == expected_path
