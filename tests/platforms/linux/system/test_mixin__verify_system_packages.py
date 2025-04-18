import subprocess
from unittest.mock import MagicMock, call

import pytest

from briefcase.console import Console
from briefcase.exceptions import BriefcaseCommandError
from briefcase.platforms.linux.system import LinuxSystemBuildCommand


@pytest.fixture
def build_command(tmp_path, first_app):
    command = LinuxSystemBuildCommand(
        console=Console(),
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
        apps={"first": first_app},
    )
    command.tools.host_os = "Linux"
    command.tools.host_arch = "wonky"

    # All calls to `shutil.which()` succeed
    command.tools.shutil.which = MagicMock(return_value="/path/to/exe")

    # Mock subprocess
    command.tools.subprocess = MagicMock()

    return command


def test_deb_requirements(build_command, first_app_config):
    """Debian requirements can be verified."""
    first_app_config.target_vendor_base = "debian"

    build_command.verify_system_packages(first_app_config)

    # The packages were verified
    assert build_command.tools.subprocess.check_output.mock_calls == [
        call(["dpkg", "-s", "python3-dev"], quiet=1),
        call(["dpkg", "-s", "dpkg-dev"], quiet=1),
        call(["dpkg", "-s", "g++"], quiet=1),
        call(["dpkg", "-s", "gcc"], quiet=1),
        call(["dpkg", "-s", "libc6-dev"], quiet=1),
        call(["dpkg", "-s", "make"], quiet=1),
    ]


def test_rpm_requirements(build_command, first_app_config):
    """RHEL requirements can be verified."""
    first_app_config.target_vendor_base = "rhel"

    build_command.verify_system_packages(first_app_config)

    assert build_command.tools.subprocess.check_output.mock_calls == [
        call(["rpm", "-q", "python3-devel"], quiet=1),
        call(["rpm", "-q", "gcc"], quiet=1),
        call(["rpm", "-q", "make"], quiet=1),
        call(["rpm", "-q", "pkgconf-pkg-config"], quiet=1),
    ]


def test_suse_requirements(build_command, first_app_config):
    """SUSE requirements can be verified."""
    first_app_config.target_vendor_base = "suse"

    build_command.verify_system_packages(first_app_config)

    assert build_command.tools.subprocess.check_output.mock_calls == [
        call(["rpm", "-q", "--whatprovides", "python3-devel"], quiet=1),
        call(
            ["rpm", "-q", "--whatprovides", "patterns-devel-base-devel_basis"], quiet=1
        ),
    ]


def test_arch_requirements(build_command, first_app_config, capsys):
    """Arch requirements can be verified."""
    first_app_config.target_vendor_base = "arch"

    build_command.verify_system_packages(first_app_config)

    assert build_command.tools.subprocess.check_output.mock_calls == [
        call(["pacman", "-Q", "python3"], quiet=1),
        call(["pacman", "-Q", "base-devel"], quiet=1),
    ]


def test_unknown_requirements(build_command, first_app_config, capsys):
    """An unknown system can't be verified."""
    first_app_config.target_vendor_base = "somevendor"

    build_command.verify_system_packages(first_app_config)

    # No packages verified
    build_command.tools.subprocess.check_output.assert_not_called()

    # A warning was logged.
    output = capsys.readouterr().out
    assert "WARNING: Can't verify system packages" in output


def test_missing_packages(build_command, first_app_config, capsys):
    """If there are missing system packages, an error is raised."""
    # Mock the system requirement tools; there's a base requirement of packages called
    # "compiler" and "compiler++", plus 3 packages provided by an installation alias
    # "alias". These packages are verified using "check <pkg>", and installed using
    # "system install_flag <pkg>"
    build_command._system_requirement_tools = MagicMock(
        return_value=(
            [
                "compiler",
                "compiler++",
                # Three packages provided by the `alias` alias
                ("aliased-1", "alias"),
                ("aliased-2", "alias"),
                ("aliased-3", "alias"),
            ],
            ["check"],
            ["system", "install_flag"],
        )
    )

    # Add some system requirements.
    first_app_config.system_requires = ["first", "second", "third"]

    # Mock the side effect of checking those requirements.
    build_command.tools.subprocess.check_output.side_effect = [
        subprocess.CalledProcessError(cmd="check", returncode=1),  # compiler
        "installed",  # compiler++
        subprocess.CalledProcessError(cmd="check", returncode=1),  # aliased-1
        "installed",  # aliased-2
        subprocess.CalledProcessError(cmd="check", returncode=1),  # aliased-3
        "installed",  # first
        subprocess.CalledProcessError(cmd="check", returncode=1),  # second
        "installed",  # third
    ]

    # Verify the requirements. This will raise an error, but the error
    # message will tell you how to install the system packages. This includes
    # using an alias for the install of aliased-1 and aliased-3.
    with pytest.raises(
        BriefcaseCommandError,
        match=r"    sudo system install_flag alias compiler second",
    ):
        build_command.verify_system_packages(first_app_config)


def test_missing_system_verify(build_command, first_app_config, capsys):
    """If the program to verify system packages doesn't exist, a warning is logged."""
    # Mock the system verifier is missing
    build_command.tools.shutil.which = MagicMock(return_value="")

    build_command.verify_system_packages(first_app_config)

    # No packages verified
    build_command.tools.subprocess.check_output.assert_not_called()

    # A warning was logged.
    output = capsys.readouterr().out
    assert "WARNING: Can't verify system packages" in output


def test_packages_installed(build_command, first_app_config, capsys):
    """If all required packages are installed, no error is raised."""
    # Mock the system requirement tools; there's a base requirement of
    # a packaged called "compiler", verified using "check <pkg>", and
    # installed using "system <pkg>"
    build_command._system_requirement_tools = MagicMock(
        return_value=(
            ["compiler"],
            ["check"],
            ["system", "install_flag"],
        )
    )

    # Add some system requirements.
    first_app_config.system_requires = ["first", "second", "third"]

    # Mock the effect of checking requirements that are all present
    build_command.tools.subprocess.check_output.return_value = "installed"

    # Verify the requirements. This will raise an error.
    build_command.verify_system_packages(first_app_config)

    assert build_command.tools.subprocess.check_output.mock_calls == [
        call(["check", "compiler"], quiet=1),
        call(["check", "first"], quiet=1),
        call(["check", "second"], quiet=1),
        call(["check", "third"], quiet=1),
    ]
