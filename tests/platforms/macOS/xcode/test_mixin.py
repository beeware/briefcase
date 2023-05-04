import pytest

from briefcase.console import Console, Log
from briefcase.exceptions import UnsupportedHostError
from briefcase.platforms.macOS.xcode import macOSXcodeCreateCommand


@pytest.fixture
def create_command(tmp_path):
    return macOSXcodeCreateCommand(
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
        match="macOS applications require the Xcode command line tools, which are only available on macOS.",
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
        / "xcode"
        / "build"
        / "Release"
        / "First App.app"
    )
    assert binary_path == expected_path


def test_project_path(create_command, first_app_config, tmp_path):
    """The project path is the Xcode project."""
    project_path = create_command.project_path(first_app_config)

    expected_path = (
        tmp_path
        / "base_path"
        / "build"
        / "first-app"
        / "macos"
        / "xcode"
        / "First App.xcodeproj"
    )
    assert expected_path == project_path
