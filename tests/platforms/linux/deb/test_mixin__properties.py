import pytest

from briefcase.console import Console, Log
from briefcase.platforms.linux.deb import LinuxDebBuildCommand


@pytest.mark.parametrize(
    "host_arch, deb_arch",
    [
        ("x86_64", "amd64"),
    ],
)
def test_deb_arch(create_command, host_arch, deb_arch):
    """Host architectures are transformed to Debian-accepted values."""
    create_command.tools.host_arch = host_arch
    assert create_command.deb_arch == deb_arch


@pytest.mark.parametrize(
    "vendor, codename, python_source, python_tag, source_tag",
    [
        ("ubuntu", "jammy", "system", "3.X", "system"),
        ("ubuntu", "jammy", "deadsnakes", "3.X", "deadsnakes-py3.X"),
        ("debian", "bullseye", "system", "3.12", "system"),
    ],
)
def test_bundle_path(
    create_command,
    first_app_config,
    vendor,
    codename,
    python_source,
    python_tag,
    source_tag,
    tmp_path,
):
    """The bundle path contains vendor and Python source details."""
    first_app_config.target_vendor = vendor
    first_app_config.target_codename = codename
    first_app_config.python_source = python_source
    first_app_config.python_version_tag = python_tag

    assert (
        create_command.bundle_path(first_app_config)
        == tmp_path
        / "base_path"
        / "linux"
        / vendor
        / codename
        / source_tag
        / "First App"
    )


@pytest.mark.parametrize(
    "vendor, codename, python_source, python_tag, arch, source_tag",
    [
        ("ubuntu", "jammy", "system", "3.X", "x86_64", "system"),
        ("ubuntu", "jammy", "deadsnakes", "3.X", "x86_64", "deadsnakes-py3.X"),
        ("debian", "bullseye", "system", "3.12", "x86_64", "system"),
    ],
)
def test_package_path(
    create_command,
    first_app_config,
    vendor,
    codename,
    python_source,
    python_tag,
    arch,
    source_tag,
    tmp_path,
):
    """The package path contains vendor and Python source details."""
    create_command.tools.host_arch = arch

    first_app_config.target_vendor = vendor
    first_app_config.target_codename = codename
    first_app_config.python_source = python_source
    first_app_config.python_version_tag = python_tag

    assert (
        create_command.package_path(first_app_config)
        == tmp_path
        / "base_path"
        / "linux"
        / vendor
        / codename
        / source_tag
        / "First App"
        / "first-app_0.0.1-1_amd64"
    )


def test_binary_path(create_command, first_app_config, tmp_path):
    """The binary path contains vendor and Python source details."""
    # Force the architecture to x86_64 for test purposes.
    create_command.tools.host_arch = "x86_64"

    # Force a dummy vendor:codename for test purposes.
    first_app_config.target_vendor = "somevendor"
    first_app_config.target_codename = "surprising"
    first_app_config.python_source = "system"

    assert (
        create_command.binary_path(first_app_config)
        == tmp_path
        / "base_path"
        / "linux"
        / "somevendor"
        / "surprising"
        / "system"
        / "First App"
        / "first-app_0.0.1-1_amd64"
        / "usr"
        / "bin"
        / "first-app"
    )


def test_distribution_path(create_command, first_app_config, tmp_path):
    """The distribution path contains vendor details."""
    # Force the architecture to x86_64 for test purposes.
    create_command.tools.host_arch = "x86_64"

    # Force a dummy vendor:codename for test purposes.
    first_app_config.target_vendor = "somevendor"
    first_app_config.target_codename = "surprising"
    first_app_config.python_source = "system"

    assert (
        create_command.distribution_path(first_app_config, "deb")
        == tmp_path
        / "base_path"
        / "linux"
        / "first-app_0.0.1-1~somevendor-surprising_amd64.deb"
    )


@pytest.mark.parametrize(
    "vendor, codename, python_source, python_tag, arch, source_tag",
    [
        ("ubuntu", "jammy", "system", "3.X", "x86_64", "system"),
        ("ubuntu", "jammy", "deadsnakes", "3.X", "x86_64", "deadsnakes-py3.X"),
        ("debian", "bullseye", "system", "3.12", "x86_64", "system"),
    ],
)
def test_docker_image_tag(
    create_command,
    first_app_config,
    vendor,
    codename,
    python_source,
    python_tag,
    arch,
    source_tag,
    tmp_path,
):
    """The docker image tag contains vendor and Python source details."""
    create_command.tools.host_arch = arch

    first_app_config.target_vendor = vendor
    first_app_config.target_codename = codename
    first_app_config.python_source = python_source
    first_app_config.python_version_tag = python_tag

    assert (
        create_command.docker_image_tag(first_app_config)
        == f"briefcase/com.example.first-app:{vendor}-{codename}-{source_tag}"
    )


@pytest.mark.parametrize(
    "vendor, codename, python_source, python_tag, arch, source_tag",
    [
        ("ubuntu", "jammy", "system", "3.X", "x86_64", "system"),
        ("ubuntu", "jammy", "deadsnakes", "3.X", "x86_64", "deadsnakes-py3.X"),
        ("debian", "bullseye", "system", "3.12", "x86_64", "system"),
    ],
)
def test_docker_image_tag_uppercase_name(
    create_command,
    uppercase_app_config,
    vendor,
    codename,
    python_source,
    python_tag,
    arch,
    source_tag,
    tmp_path,
):
    create_command.tools.host_arch = arch

    uppercase_app_config.target_vendor = vendor
    uppercase_app_config.target_codename = codename
    uppercase_app_config.python_source = python_source
    uppercase_app_config.python_version_tag = python_tag

    assert (
        create_command.docker_image_tag(uppercase_app_config)
        == f"briefcase/com.example.first-app:{vendor}-{codename}-{source_tag}"
    )


def test_clone_options(create_command, tmp_path):
    """Docker options are cloned."""
    build_command = LinuxDebBuildCommand(
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
