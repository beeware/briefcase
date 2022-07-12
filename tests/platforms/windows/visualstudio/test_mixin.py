from briefcase.platforms.windows.visualstudio import WindowsVisualStudioCreateCommand


def test_binary_path(first_app_config, tmp_path):
    command = WindowsVisualStudioCreateCommand(base_path=tmp_path)
    binary_path = command.binary_path(first_app_config)

    assert (
        binary_path
        == tmp_path
        / "windows"
        / "VisualStudio"
        / "First App"
        / "x64"
        / "Release"
        / "First App.exe"
    )


def test_distribution_path(first_app_config, tmp_path):
    command = WindowsVisualStudioCreateCommand(base_path=tmp_path)
    distribution_path = command.distribution_path(first_app_config, "app")

    assert distribution_path == tmp_path / "windows" / "First App-0.0.1.msi"
