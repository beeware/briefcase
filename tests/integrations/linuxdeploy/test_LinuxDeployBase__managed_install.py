import pytest

from briefcase.integrations.linuxdeploy import LinuxDeployBase


@pytest.fixture
def linuxdeploy(mock_tools, tmp_path):
    class LinuxDeployDummy(LinuxDeployBase):
        name = "dummy-plugin"

        @property
        def file_name(self):
            return "linuxdeploy-dummy-wonky.AppImage"

        @property
        def download_url(self):
            return "https://example.com/path/to/linuxdeploy-dummy-wonky.AppImage"

        @property
        def file_path(self):
            return tmp_path / "plugin"

    return LinuxDeployDummy(mock_tools)


def test_managed_install_is_true(linuxdeploy):
    """LinuxDeployBase.managed_install is True."""
    assert linuxdeploy.managed_install is True
