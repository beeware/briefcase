import sys

import pytest

from briefcase.console import Console, Log
from briefcase.exceptions import BriefcaseCommandError
from briefcase.platforms.iOS.xcode import iOSXcodeCreateCommand


@pytest.fixture
def create_command(tmp_path):
    return iOSXcodeCreateCommand(
        logger=Log(),
        console=Console(),
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )


def test_binary_path(create_command, first_app_config, tmp_path):
    binary_path = create_command.binary_path(first_app_config)

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


def test_distribution_path(create_command, first_app_config, tmp_path):
    distribution_path = create_command.distribution_path(
        first_app_config,
        packaging_format="any",
    )

    assert distribution_path == (
        tmp_path
        / "base_path"
        / "iOS"
        / "Xcode"
        / "First App"
        / "build"
        / "Debug-iphonesimulator"
        / "First App.app"
    )


@pytest.mark.skipif(sys.platform == "darwin", reason="non-macOS specific test")
def test_verify_non_macOS(create_command):
    "If you're not on macOS, you can't verify tools."

    with pytest.raises(
        BriefcaseCommandError,
        match="iOS applications require Xcode, which is only available on macOS.",
    ):
        create_command.verify_tools()
