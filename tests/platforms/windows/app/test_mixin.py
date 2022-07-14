from briefcase.platforms.windows.app import WindowsAppCreateCommand


def test_binary_path(first_app_config, tmp_path):
    command = WindowsAppCreateCommand(base_path=tmp_path)
    binary_path = command.binary_path(first_app_config)

    assert (
        binary_path
        == tmp_path / "windows" / "app" / "First App" / "src" / "First App.exe"
    )


def test_distribution_path(first_app_config, tmp_path):
    command = WindowsAppCreateCommand(base_path=tmp_path)
    distribution_path = command.distribution_path(first_app_config, "app")

    assert distribution_path == tmp_path / "windows" / "First App-0.0.1.msi"
