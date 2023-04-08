import pytest


@pytest.mark.parametrize(
    "support_revision, host_arch, url",
    [
        (
            "3.10.9+20230116",
            "x86_64",
            "20230116/cpython-3.10.9+20230116-x86_64-unknown-linux-gnu-install_only.tar.gz",
        ),
        (
            "3.11.1+20230116",
            "aarch64",
            "20230116/cpython-3.11.1+20230116-aarch64-unknown-linux-gnu-install_only.tar.gz",
        ),
        (
            "3.8.16+20221220",
            "x86_64",
            "20221220/cpython-3.8.16+20221220-x86_64-unknown-linux-gnu-install_only.tar.gz",
        ),
    ],
)
def test_support_package_url(
    linux_mixin,
    host_arch,
    support_revision,
    url,
):
    """The support package URL is customized."""
    # Set up the host architecture
    linux_mixin.tools.host_arch = host_arch

    assert linux_mixin.support_package_url(support_revision) == (
        "https://github.com/indygreg/python-build-standalone/releases/download/" + url
    )
