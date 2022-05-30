from unittest.mock import MagicMock

from briefcase.integrations.linuxdeploy import LinuxDeploy


def test_managed_install():
    """All linuxdeploy installs are managed."""
    linuxdeploy = LinuxDeploy(MagicMock())

    assert linuxdeploy.managed_install
