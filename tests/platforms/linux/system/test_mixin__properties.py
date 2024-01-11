from unittest.mock import MagicMock

import pytest

from briefcase.console import Console, Log
from briefcase.exceptions import BriefcaseCommandError
from briefcase.platforms.linux.system import LinuxSystemBuildCommand


@pytest.mark.parametrize(
    "vendor, codename",
    [
        ("ubuntu", "jammy"),
        ("debian", "bullseye"),
    ],
)
def test_build_path(
    create_command,
    first_app_config,
    vendor,
    codename,
    tmp_path,
):
    """The bundle path contains vendor and Python source details."""
    first_app_config.target_vendor = vendor
    first_app_config.target_codename = codename

    assert (
        create_command.build_path(first_app_config)
        == tmp_path / "base_path/build/first-app" / vendor
    )


@pytest.mark.parametrize(
    "vendor, codename",
    [
        ("ubuntu", "jammy"),
        ("debian", "bullseye"),
    ],
)
def test_bundle_path(
    create_command,
    first_app_config,
    vendor,
    codename,
    tmp_path,
):
    """The bundle path contains vendor and Python source details."""
    first_app_config.target_vendor = vendor
    first_app_config.target_codename = codename

    assert (
        create_command.bundle_path(first_app_config)
        == tmp_path / "base_path/build/first-app" / vendor / codename
    )


def test_binary_path(create_command, first_app_config, tmp_path):
    """The binary path contains vendor and Python source details."""
    # Force the architecture to x86_64 for test purposes.
    create_command.tools.host_arch = "x86_64"

    # Force a dummy vendor:codename for test purposes.
    first_app_config.target_vendor = "somevendor"
    first_app_config.target_codename = "surprising"

    assert (
        create_command.binary_path(first_app_config)
        == tmp_path
        / "base_path"
        / "build"
        / "first-app"
        / "somevendor"
        / "surprising"
        / "first-app-0.0.1"
        / "usr"
        / "bin"
        / "first-app"
    )


@pytest.mark.parametrize(
    "packaging_format, vendor_base, filename",
    [
        ("deb", "debian", "first-app_0.0.1-1~somevendor-surprising_wonky.deb"),
        ("rpm", "fedora", "first-app-0.0.1-1.elsurprising.wonky.rpm"),
        ("rpm", "suse", "first-app-0.0.1-1.wonky.rpm"),
        ("pkg", "arch", "first-app-0.0.1-1-wonky.pkg.tar.zst"),
    ],
)
def test_distribution_path(
    create_command,
    first_app_config,
    packaging_format,
    vendor_base,
    filename,
    tmp_path,
):
    """The distribution path contains vendor details."""
    # Mock return value for ABI from packaging system
    create_command._build_env_abi = MagicMock(return_value="wonky")

    # Set vendor base (RPM package naming changes for openSUSE)
    first_app_config.target_vendor_base = vendor_base

    # Force a dummy vendor:codename for test purposes.
    first_app_config.target_vendor = "somevendor"
    first_app_config.target_codename = "surprising"
    first_app_config.packaging_format = packaging_format

    assert (
        create_command.distribution_path(first_app_config)
        == tmp_path / "base_path/dist" / filename
    )


def test_distribution_path_unknown(create_command, first_app_config, tmp_path):
    """If the packaging format isn't known, an error is raised."""
    # Force the architecture to x86_64 for test purposes.
    create_command.tools.host_arch = "x86_64"

    # Force a dummy vendor:codename for test purposes.
    first_app_config.target_vendor = "somevendor"
    first_app_config.target_codename = "surprising"
    first_app_config.packaging_format = "unknown"

    with pytest.raises(
        BriefcaseCommandError,
        match=r"Briefcase doesn't currently know how to build system packages in UNKNOWN format.",
    ):
        create_command.distribution_path(first_app_config)


@pytest.mark.parametrize(
    "vendor, codename",
    [
        ("ubuntu", "jammy"),
        ("debian", "bullseye"),
    ],
)
def test_docker_image_tag(
    create_command,
    first_app_config,
    vendor,
    codename,
    tmp_path,
):
    """The docker image tag contains vendor and Python source details."""
    first_app_config.target_vendor = vendor
    first_app_config.target_codename = codename

    assert (
        create_command.docker_image_tag(first_app_config)
        == f"briefcase/com.example.first-app:{vendor}-{codename}"
    )


def test_docker_image_tag_uppercase_name(
    create_command,
    uppercase_app_config,
    tmp_path,
):
    uppercase_app_config.target_vendor = "somevendor"
    uppercase_app_config.target_codename = "surprising"

    assert (
        create_command.docker_image_tag(uppercase_app_config)
        == "briefcase/com.example.first-app:somevendor-surprising"
    )


def test_clone_options(create_command, tmp_path):
    """Docker options are cloned."""
    build_command = LinuxSystemBuildCommand(
        logger=Log(),
        console=Console(),
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )
    build_command.target_image = "somevendor:surprising"

    create_command = build_command.create_command

    # Confirm the use_docker option has been cloned.
    assert create_command.is_clone
    assert create_command.target_image == "somevendor:surprising"
