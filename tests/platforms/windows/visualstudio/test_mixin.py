import pytest

from briefcase.console import Console, Log
from briefcase.exceptions import UnsupportedHostError
from briefcase.platforms.windows.visualstudio import WindowsVisualStudioCreateCommand


@pytest.fixture
def create_command(tmp_path):
    return WindowsVisualStudioCreateCommand(
        logger=Log(),
        console=Console(),
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )


@pytest.mark.parametrize("host_os", ["Darwin", "Linux", "WeirdOS"])
def test_unsupported_host_os(create_command, host_os):
    """Error raised for an unsupported OS."""
    create_command.tools.host_os = host_os

    with pytest.raises(
        UnsupportedHostError,
        match="Windows applications can only be built on Windows.",
    ):
        create_command()


def test_binary_path(create_command, first_app_config, tmp_path):
    binary_path = create_command.binary_path(first_app_config)

    assert (
        binary_path
        == tmp_path
        / "base_path"
        / "build"
        / "first-app"
        / "windows"
        / "visualstudio"
        / "x64"
        / "Release"
        / "First App.exe"
    )


def test_project_path(create_command, first_app_config, tmp_path):
    """The project path is the Visual Studio solution."""
    project_path = create_command.project_path(first_app_config)

    expected_path = (
        tmp_path
        / "base_path"
        / "build"
        / "first-app"
        / "windows"
        / "visualstudio"
        / "First App.sln"
    )
    assert expected_path == project_path


def test_distribution_path(create_command, first_app_config, tmp_path):
    distribution_path = create_command.distribution_path(first_app_config)

    assert distribution_path == tmp_path / "base_path/dist/First App-0.0.1.msi"
