from briefcase.console import Console, Log
from briefcase.platforms.iOS.xcode import iOSXcodeCreateCommand


def test_binary_path(first_app_config, tmp_path):
    command = iOSXcodeCreateCommand(
        logger=Log(),
        console=Console(),
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )
    binary_path = command.binary_path(first_app_config)

    assert binary_path == (
        tmp_path
        / "base_path"
        / "iOS"
        / "Xcode"
        / "First App"
        / "build"
        / "Debug-iphonesimulator"
        / "First App.app"
    )


def test_distribution_path(first_app_config, tmp_path):
    command = iOSXcodeCreateCommand(
        logger=Log(),
        console=Console(),
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )
    binary_path = command.binary_path(first_app_config)

    assert binary_path == (
        tmp_path
        / "base_path"
        / "iOS"
        / "Xcode"
        / "First App"
        / "build"
        / "Debug-iphonesimulator"
        / "First App.app"
    )
