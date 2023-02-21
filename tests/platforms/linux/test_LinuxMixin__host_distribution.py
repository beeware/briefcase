import subprocess
from unittest.mock import MagicMock

import pytest

from briefcase.exceptions import BriefcaseCommandError
from briefcase.platforms import linux

from ...utils import create_file


@pytest.fixture
def _Path(monkeypatch, tmp_path):
    """Mock a Path() constructor so that any requested file is redirected
    to same path, but under tmp_path
    """
    mock_Path = MagicMock()
    mock_Path.side_effect = lambda path: tmp_path / path[1:]
    monkeypatch.setattr(linux, "Path", mock_Path)
    return mock_Path


@pytest.fixture
def linux_mixin():
    "A Linux mixin with a mocked tools collection"
    linux_mixin = linux.LinuxMixin()
    linux_mixin.tools = MagicMock()
    return linux_mixin


@pytest.mark.parametrize(
    "release_files, distribution, version",
    [
        # Redhat derivatives
        (
            {
                "redhat": "Red Hat Enterprise Linux release 8.7 (Ootpa)\n",
            },
            "redhat",
            "8",
        ),
        (
            {
                "redhat": "Fedora release 34 (thirtyfour)\n",
                "fedora": "Fedora release 34 (thirtyfour)\n",
            },
            "fedora",
            "34",
        ),
        (
            {
                "redhat": "CentOS Linux release 8.4.2105\n",
                "centos": "CentOS Linux release 8.4.2105\n",
            },
            "centos",
            "8",
        ),
        (
            {
                "redhat": "AlmaLinux release 8.7 (Stone Smilodon)\n",
                "almalinux": "AlmaLinux release 8.7 (Stone Smilodon)\n",
            },
            "almalinux",
            "8",
        ),
        # Arch derivatives
        (
            {
                "arch": "",
            },
            "archlinux",
            "latest",
        ),
        (
            {
                "arch": "Manjaro Linux\n",
            },
            "manjarolinux",
            "latest",
        ),
    ],
)
def test_host_distribution_release_file(
    linux_mixin, _Path, release_files, distribution, version, tmp_path
):
    """The host vendor can be identified using release files."""
    # Create the identifying release files
    for distro, content in release_files.items():
        create_file(tmp_path / "etc" / f"{distro}-release", content)

    # Check the distribution is identified correctly
    assert linux_mixin.host_distribution() == (distribution, version)

    # Assert that lsb_release wasn't invoked.
    linux_mixin.tools.subprocess.check_output.assert_not_called()


@pytest.mark.parametrize(
    "release_files, message",
    [
        (
            {"redhat"},
            r"Unable to parse Red Hat Enterprise Linux release "
            r"from /etc/redhat-release content.",
        ),
        (
            {"redhat", "fedora"},
            r"Unable to parse Fedora release from /etc/fedora-release.",
        ),
        (
            {"redhat", "centos"},
            r"Unable to parse Centos release from /etc/centos-release.",
        ),
        (
            {"redhat", "almalinux"},
            r"Unable to parse AlmaLinux release from /etc/almalinux-release content.",
        ),
        (
            {"arch"},
            r"Unable to identify the specific arch-based Linux distribution "
            r"from /etc/arch-release content.",
        ),
    ],
)
def test_host_distribution_bad_release_file(
    linux_mixin, _Path, release_files, message, tmp_path
):
    """Unexpected/unparseable content in a release file raises an error."""
    # Create the identifying release files
    for distro in release_files:
        create_file(tmp_path / "etc" / f"{distro}-release", "badcontent")

    # Check the distribution is identified correctly
    with pytest.raises(BriefcaseCommandError, match=message):
        linux_mixin.host_distribution()

    # Assert that lsb_release wasn't invoked.
    linux_mixin.tools.subprocess.check_output.assert_not_called()


def test_host_distribution_lsb_release(linux_mixin, _Path):
    "If no /etc/*-release files can be found, fall back to lsb_release"
    # Mock the response of lsb_release
    linux_mixin.tools.subprocess.check_output.side_effect = [
        "somevendor",
        "surprising",
    ]

    # Check the distribution is identified correctly
    assert linux_mixin.host_distribution() == ("somevendor", "surprising")


def test_host_distribution_no_lsb_release(linux_mixin, _Path):
    "If lsb_release doesn't exist, we can't identify the version"
    # Mock the response when lsb_release doesn't exist
    linux_mixin.tools.subprocess.check_output.side_effect = (
        subprocess.CalledProcessError(cmd="lsbrelease", returncode=2)
    )

    # Check the distribution is identified correctly
    with pytest.raises(
        BriefcaseCommandError,
        match=r"Unable to identify the vendor of your Linux system using `lsb_release`.",
    ):
        linux_mixin.host_distribution()
