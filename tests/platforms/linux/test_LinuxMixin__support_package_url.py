import pytest


@pytest.mark.parametrize(
    "support_revision, host_arch, is_32bit_python, url",
    [
        (
            "3.10.9+20230116",
            "x86_64",
            False,
            "20230116/cpython-3.10.9+20230116-x86_64-unknown-linux-gnu-install_only.tar.gz",
        ),
        (
            "3.11.1+20230116",
            "aarch64",
            False,
            "20230116/cpython-3.11.1+20230116-aarch64-unknown-linux-gnu-install_only.tar.gz",
        ),
        (
            "3.11.1+20230116",
            "aarch64",
            True,
            "20230116/cpython-3.11.1+20230116-armv7-unknown-linux-gnu-install_only.tar.gz",
        ),
        (
            "3.11.1+20230116",
            "armv7l",
            True,
            "20230116/cpython-3.11.1+20230116-armv7l-unknown-linux-gnu-install_only.tar.gz",
        ),
        (
            "3.8.16+20221220",
            "x86_64",
            False,
            "20221220/cpython-3.8.16+20221220-x86_64-unknown-linux-gnu-install_only.tar.gz",
        ),
        (
            "3.8.16+20221220",
            "x86_64",
            True,
            "20221220/cpython-3.8.16+20221220-i686-unknown-linux-gnu-install_only.tar.gz",
        ),
        (
            "3.8.16+20221220",
            "i686",
            True,
            "20221220/cpython-3.8.16+20221220-i686-unknown-linux-gnu-install_only.tar.gz",
        ),
    ],
)
def test_support_package_url(
    linux_mixin,
    host_arch,
    support_revision,
    is_32bit_python,
    url,
):
    """The support package URL is customized."""
    # Set up the host architecture
    linux_mixin.tools.host_arch = host_arch
    linux_mixin.tools.is_32bit_python = is_32bit_python

    assert linux_mixin.support_package_url(support_revision) == (
        "https://github.com/indygreg/python-build-standalone/releases/download/" + url
    )
