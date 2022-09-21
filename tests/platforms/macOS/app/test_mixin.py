from briefcase.console import Console, Log
from briefcase.platforms.macOS.app import macOSAppCreateCommand


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


def test_entitlements_path(first_app_config, tmp_path):
    command = macOSAppCreateCommand(
        logger=Log(),
        console=Console(),
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )
    entitlements_path = command.entitlements_path(first_app_config)

    assert (
        entitlements_path
        == tmp_path / "base_path" / "macOS" / "app" / "First App" / "Entitlements.plist"
    )
