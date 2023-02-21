import pytest

from briefcase.platforms.linux import LinuxMixin


@pytest.mark.parametrize(
    "vendor, base",
    [
        # Debian derivatives
        ("debian", "debian"),
        ("ubuntu", "debian"),
        # Redhat derivatives
        ("redhat", "redhat"),
        ("fedora", "redhat"),
        ("centos", "redhat"),
        ("almalinux", "redhat"),
        # Arch derivatives
        ("archlinux", "archlinux"),
        ("manjarolinux", "archlinux"),
        # Unknown
        ("unknown", None),
    ],
)
def test_vendor_base(vendor, base):
    """The host vendor can be identified."""
    assert LinuxMixin().vendor_base(vendor) == base
