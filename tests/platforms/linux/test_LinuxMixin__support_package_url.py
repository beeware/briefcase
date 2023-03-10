import pytest


@pytest.mark.parametrize(
    "support_revision, url",
    [
        (
            "3.10.9+20230116",
            "20230116/cpython-3.10.9+20230116-x86_64-unknown-linux-gnu-install_only.tar.gz",
        ),
        (
            "3.11.1+20230116",
            "20230116/cpython-3.11.1+20230116-x86_64-unknown-linux-gnu-install_only.tar.gz",
        ),
        (
            "3.8.16+20221220",
            "20221220/cpython-3.8.16+20221220-x86_64-unknown-linux-gnu-install_only.tar.gz",
        ),
    ],
)
def test_support_package_url(
    linux_mixin,
    support_revision,
    url,
):
    """The support package URL is customized."""
    assert linux_mixin.support_package_url(support_revision) == (
        "https://github.com/indygreg/python-build-standalone/releases/download/" + url
    )
