def test_managed_install(mock_tools, rcedit):
    """All rcedit installs are managed."""
    assert rcedit.managed_install
