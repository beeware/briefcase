from briefcase.integrations.linuxdeploy import LinuxDeployGtkPlugin, LinuxDeployQtPlugin


def test_managed_install(linuxdeploy):
    """All linuxdeploy installs are managed."""
    assert linuxdeploy.managed_install is True


def test_file_path(linuxdeploy, mock_tools):
    """Linuxdeploy resides in the tool path."""
    assert linuxdeploy.file_path == mock_tools.base_path


def test_file_name(linuxdeploy):
    """Linuxdeploy filename is architecture dependent."""
    assert linuxdeploy.file_name == "linuxdeploy-wonky.AppImage"


def test_download_url(linuxdeploy):
    """Linuxdeploy download URL is architecture dependent."""
    assert linuxdeploy.download_url == (
        "https://github.com/linuxdeploy/linuxdeploy/"
        "releases/download/continuous/linuxdeploy-wonky.AppImage"
    )


def test_plugins(linuxdeploy):
    """There are 2 known plugins."""
    assert linuxdeploy.plugins == {
        "gtk": LinuxDeployGtkPlugin,
        "qt": LinuxDeployQtPlugin,
    }
