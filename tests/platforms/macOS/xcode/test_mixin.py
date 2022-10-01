import sys

import pytest

from briefcase.console import Console, Log
from briefcase.exceptions import BriefcaseCommandError
from briefcase.platforms.macOS.xcode import macOSXcodeCreateCommand


@pytest.fixture
def create_command(tmp_path):
    return macOSXcodeCreateCommand(
        logger=Log(),
        console=Console(),
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )


def test_binary_path(create_command, first_app_config, tmp_path):
    binary_path = create_command.binary_path(first_app_config)

    assert (
        binary_path
        == tmp_path
        / "base_path"
        / "macOS"
        / "Xcode"
        / "First App"
        / "build"
        / "Release"
        / "First App.app"
    )


def test_distribution_path_app(create_command, first_app_config, tmp_path):
    distribution_path = create_command.distribution_path(first_app_config, "app")

    assert (
        distribution_path
        == tmp_path
        / "base_path"
        / "macOS"
        / "Xcode"
        / "First App"
        / "build"
        / "Release"
        / "First App.app"
    )


def test_distribution_path_dmg(create_command, first_app_config, tmp_path):
    distribution_path = create_command.distribution_path(first_app_config, "dmg")

    assert distribution_path == tmp_path / "base_path" / "macOS" / "First App-0.0.1.dmg"


def test_entitlements_path(create_command, first_app_config, tmp_path):
    entitlements_path = create_command.entitlements_path(first_app_config)

    assert (
        entitlements_path
        == tmp_path
        / "base_path"
        / "macOS"
        / "Xcode"
        / "First App"
        / "First App"
        / "first-app.entitlements"
    )


@pytest.mark.skipif(sys.platform == "darwin", reason="non-macOS specific test")
def test_verify_non_macOS(create_command):
    "If you're not on macOS, you can't verify tools."

    with pytest.raises(
        BriefcaseCommandError,
        match="macOS applications require the Xcode command line tools, "
        "which are only available on macOS.",
    ):
        create_command.verify_tools()
