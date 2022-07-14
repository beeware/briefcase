from unittest.mock import MagicMock

from briefcase.integrations.rcedit import RCEdit


def test_managed_install():
    """All rcedit installs are managed."""
    rcedit = RCEdit(MagicMock())

    assert rcedit.managed_install
