import pytest

from briefcase.console import Console, Log
from briefcase.exceptions import BriefcaseCommandError
from briefcase.platforms.macOS.app import macOSAppCreateCommand


@pytest.mark.parametrize("host_os", ["Linux", "Windows"])
def test_unsupported_host_os(host_os):
    """Error raised for an unsupported OS."""
    command = macOSAppCreateCommand(logger=Log(), console=Console())
    command.tools.host_os = host_os

    with pytest.raises(
        BriefcaseCommandError,
        match="Building and / or code signing a DMG requires running on macOS.",
    ):
        command()


def test_binary_path(first_app_config, tmp_path):
    command = macOSAppCreateCommand(
        logger=Log(),
        console=Console(),
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )
    binary_path = command.binary_path(first_app_config)

    assert (
        binary_path
        == tmp_path / "base_path" / "macOS" / "app" / "First App" / "First App.app"
    )


def test_distribution_path_app(first_app_config, tmp_path):
    command = macOSAppCreateCommand(
        logger=Log(),
        console=Console(),
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )

    distribution_path = command.distribution_path(first_app_config, "app")

    assert (
        distribution_path
        == tmp_path / "base_path" / "macOS" / "app" / "First App" / "First App.app"
    )


def test_distribution_path_dmg(first_app_config, tmp_path):
    command = macOSAppCreateCommand(
        logger=Log(),
        console=Console(),
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )

    distribution_path = command.distribution_path(first_app_config, "dmg")

    assert distribution_path == tmp_path / "base_path" / "macOS" / "First App-0.0.1.dmg"
