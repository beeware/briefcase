from briefcase.console import Console, Log
from briefcase.platforms.windows.app import WindowsAppCreateCommand


def test_binary_path(first_app_config, tmp_path):
    command = WindowsAppCreateCommand(
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
        / "windows"
        / "app"
        / "First App"
        / "src"
        / "First App.exe"
    )


def test_distribution_path(first_app_config, tmp_path):
    command = WindowsAppCreateCommand(
        logger=Log(),
        console=Console(),
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )
    distribution_path = command.distribution_path(first_app_config, "app")

    assert (
        distribution_path == tmp_path / "base_path" / "windows" / "First App-0.0.1.msi"
    )
