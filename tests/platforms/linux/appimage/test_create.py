import sys

import pytest

from briefcase.console import Console, Log
from briefcase.exceptions import UnsupportedHostError
from briefcase.platforms.linux.appimage import LinuxAppImageCreateCommand


@pytest.fixture
def create_command(first_app_config, tmp_path):
    return LinuxAppImageCreateCommand(
        logger=Log(),
        console=Console(),
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )


def test_default_options(create_command):
    """The default options are as expected."""
    options = create_command.parse_options([])

    assert options == {}

    assert create_command.use_docker


def test_options(create_command):
    """The extra options can be parsed."""
    options = create_command.parse_options(["--no-docker"])

    assert options == {}

    assert not create_command.use_docker


@pytest.mark.parametrize("host_os", ["Windows", "WeirdOS"])
def test_unsupported_host_os_with_docker(create_command, host_os):
    """Error raised for an unsupported OS when using Docker."""
    create_command.use_docker = True
    create_command.tools.host_os = host_os

    with pytest.raises(
        UnsupportedHostError,
        match="Linux AppImages can only be built on Linux, or on macOS using Docker.",
    ):
        create_command()


@pytest.mark.parametrize("host_os", ["Darwin", "Windows", "WeirdOS"])
def test_unsupported_host_os_without_docker(
    create_command,
    host_os,
):
    """Error raised for an unsupported OS when not using Docker."""
    create_command.use_docker = False
    create_command.tools.host_os = host_os

    with pytest.raises(
        UnsupportedHostError,
        match="Linux AppImages can only be built on Linux, or on macOS using Docker.",
    ):
        create_command()


def test_support_package_url(create_command):
    """The URL of the support package is predictable."""
    # Set the host arch to something predictable
    create_command.tools.host_arch = "wonky"

    revision = 52
    expected_url = (
        f"https://briefcase-support.s3.amazonaws.com/python"
        f"/3.{sys.version_info.minor}/linux/wonky"
        f"/Python-3.{sys.version_info.minor}-linux-wonky-support.b{revision}.tar.gz"
    )
    assert create_command.support_package_url(revision) == expected_url
