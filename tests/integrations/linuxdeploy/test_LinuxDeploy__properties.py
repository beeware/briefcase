from briefcase.integrations.linuxdeploy import (
    LinuxDeploy,
    LinuxDeployGtkPlugin,
    LinuxDeployQtPlugin,
)


def test_managed_install(mock_tools):
    """All linuxdeploy installs are managed."""
    linuxdeploy = LinuxDeploy(mock_tools)

    assert linuxdeploy.managed_install


def test_file_path(mock_tools):
    """Linuxdeploy resides in the tool path."""
    linuxdeploy = LinuxDeploy(mock_tools)

    assert linuxdeploy.file_path == mock_tools.base_path


def test_file_name(mock_tools):
    """Linuxdeploy filename is architecture dependent."""
    linuxdeploy = LinuxDeploy(mock_tools)

    assert linuxdeploy.file_name == "linuxdeploy-wonky.AppImage"


def test_download_url(mock_tools):
    """Linuxdeploy download URL is architecture dependent."""
    linuxdeploy = LinuxDeploy(mock_tools)

    assert linuxdeploy.download_url == (
        "https://github.com/linuxdeploy/linuxdeploy/"
        "releases/download/continuous/linuxdeploy-wonky.AppImage"
    )


def test_plugins(mock_tools):
    """There are 2 known plugins."""
    linuxdeploy = LinuxDeploy(mock_tools)

    assert linuxdeploy.plugins == {
        "gtk": LinuxDeployGtkPlugin,
        "qt": LinuxDeployQtPlugin,
    }
