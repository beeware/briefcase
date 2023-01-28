import pytest

from briefcase.console import Console, Log
from briefcase.exceptions import BriefcaseCommandError
from briefcase.platforms.windows.visualstudio import WindowsVisualStudioCreateCommand


@pytest.mark.parametrize("host_os", ["Darwin", "Linux"])
def test_unsupported_host_os(host_os):
    """Error raised for an unsupported OS."""
    command = WindowsVisualStudioCreateCommand(logger=Log(), console=Console())
    command.tools.host_os = host_os

    with pytest.raises(
        BriefcaseCommandError,
        match="Building a MSI requires running on Windows.",
    ):
        command()


def test_binary_path(first_app_config, tmp_path):
    command = WindowsVisualStudioCreateCommand(
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
        / "VisualStudio"
        / "First App"
        / "x64"
        / "Release"
        / "First App.exe"
    )


def test_distribution_path(first_app_config, tmp_path):
    command = WindowsVisualStudioCreateCommand(
        logger=Log(),
        console=Console(),
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )
    distribution_path = command.distribution_path(first_app_config, "app")

    assert (
        distribution_path == tmp_path / "base_path" / "windows" / "First App-0.0.1.msi"
    )
