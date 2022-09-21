from briefcase.integrations.rcedit import RCEdit


def test_managed_install(mock_tools):
    """All rcedit installs are managed."""
    rcedit = RCEdit(mock_tools)

    assert rcedit.managed_install
