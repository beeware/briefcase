from ...utils import assert_url_resolvable


def test_managed_install(mock_tools, rcedit):
    """All rcedit installs are managed."""
    assert rcedit.managed_install


def test_rcedit_url(mock_tools, rcedit):
    """The URL for RCEdit is correct."""
    assert (
        rcedit.download_url
        == "https://github.com/electron/rcedit/releases/download/v2.0.0/rcedit-x64.exe"
    )
    assert_url_resolvable(rcedit.download_url)
