import pytest

from briefcase.platforms.linux import parse_freedesktop_os_release

from .os_release import OS_RELEASE


@pytest.mark.parametrize(
    "docker, vendor, codename, vendor_base",
    [
        ("archlinux:latest", "arch", "rolling", "arch"),
        ("manjaro/base:latest", "manjaro", "rolling", "arch"),
        ("fedora:37", "fedora", "37", "rhel"),
        ("rhel/ubi8:8.7", "rhel", "8", "rhel"),
        ("almalinux:9.1", "almalinux", "9", "rhel"),
        ("centos:8", "centos", "8", "rhel"),
        ("opensuse/leap:15.4", "opensuse-leap", "15", "suse"),
        ("opensuse/tumbleweed:latest", "opensuse-tumbleweed", "20230304", "suse"),
        ("debian:11", "debian", "bullseye", "debian"),
        ("ubuntu:22.04", "ubuntu", "jammy", "debian"),
        ("pop:22.04", "pop", "jammy", "debian"),
        ("linuxmint:19.2", "linuxmint", "tina", "debian"),
    ],
)
def test_vendor_details(linux_mixin, docker, vendor, codename, vendor_base):
    "Assert real-world examples of vendor details work"
    assert linux_mixin.vendor_details(
        parse_freedesktop_os_release(OS_RELEASE[docker])
    ) == (
        vendor,
        codename,
        vendor_base,
    )
