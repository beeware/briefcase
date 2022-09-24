import pytest

from briefcase.console import Console, Log
from briefcase.platforms.iOS.xcode import iOSXcodePackageCommand


@pytest.fixture
def package_command(tmp_path, first_app_config):
    command = iOSXcodePackageCommand(
        logger=Log(),
        console=Console(),
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )
    command.data_path = tmp_path / "briefcase"
    return command


def test_packaging_formats(package_command):
    assert package_command.packaging_formats == ["ipa"]


def test_default_packaging_format(package_command):
    assert package_command.default_packaging_format == "ipa"
