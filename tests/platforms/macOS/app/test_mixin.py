import pytest

from briefcase.console import Console, Log
from briefcase.exceptions import UnsupportedHostError
from briefcase.platforms.macOS.app import macOSAppCreateCommand


@pytest.fixture
def create_command(tmp_path):
    return macOSAppCreateCommand(
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
        match="Building and / or code signing a DMG requires running on macOS.",
    ):
        create_command()


def test_binary_path(create_command, first_app_config, tmp_path):
    binary_path = create_command.binary_path(first_app_config)

    expected_path = (
        tmp_path / "base_path" / "macOS" / "app" / "First App" / "First App.app"
    )
    assert binary_path == expected_path


def test_distribution_path_app(create_command, first_app_config, tmp_path):
    distribution_path = create_command.distribution_path(first_app_config, "app")

    expected_path = (
        tmp_path / "base_path" / "macOS" / "app" / "First App" / "First App.app"
    )
    assert distribution_path == expected_path


def test_distribution_path_dmg(create_command, first_app_config, tmp_path):
    distribution_path = create_command.distribution_path(first_app_config, "dmg")

    expected_path = tmp_path / "base_path" / "macOS" / "First App-0.0.1.dmg"
    assert distribution_path == expected_path
