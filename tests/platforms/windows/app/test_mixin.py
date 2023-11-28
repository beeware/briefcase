import pytest

from briefcase.console import Console, Log
from briefcase.platforms.windows.app import WindowsAppCreateCommand


@pytest.fixture
def create_command(tmp_path):
    return WindowsAppCreateCommand(
        logger=Log(),
        console=Console(),
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )


def test_binary_path(create_command, first_app_config, tmp_path):
    binary_path = create_command.binary_path(first_app_config)

    expected_path = (
        tmp_path
        / "base_path"
        / "build"
        / "first-app"
        / "windows"
        / "app"
        / "src"
        / "First App.exe"
    )
    assert binary_path == expected_path


def test_project_path(create_command, first_app_config, tmp_path):
    """The project path is the bundle path."""
    project_path = create_command.project_path(first_app_config)
    bundle_path = create_command.bundle_path(first_app_config)

    expected_path = tmp_path / "base_path/build/first-app/windows/app"
    assert expected_path == project_path == bundle_path


def test_distribution_path(create_command, first_app_config, tmp_path):
    distribution_path = create_command.distribution_path(first_app_config)

    expected_path = tmp_path / "base_path/dist/First App-0.0.1.msi"
    assert distribution_path == expected_path
