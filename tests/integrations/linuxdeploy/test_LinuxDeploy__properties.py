from briefcase.integrations.linuxdeploy import (
    LinuxDeploy,
    LinuxDeployGtkPlugin,
    LinuxDeployQtPlugin,
)


def test_managed_install(mock_command):
    """All linuxdeploy installs are managed."""
    linuxdeploy = LinuxDeploy(mock_command)

    assert linuxdeploy.managed_install


def test_file_path(mock_command):
    """Linuxdeploy resides in the tool path."""
    linuxdeploy = LinuxDeploy(mock_command)

    assert linuxdeploy.file_path == mock_command.tools_path


def test_file_name(mock_command):
    """Linuxdeploy filename is architecture dependent."""
    linuxdeploy = LinuxDeploy(mock_command)

    assert linuxdeploy.file_name == "linuxdeploy-wonky.AppImage"


def test_download_url(mock_command):
    """Linuxdeploy download URL is architecture dependent."""
    linuxdeploy = LinuxDeploy(mock_command)

    assert linuxdeploy.download_url == (
        "https://github.com/linuxdeploy/linuxdeploy/"
        "releases/download/continuous/linuxdeploy-wonky.AppImage"
    )


def test_plugins(mock_command):
    """There are 2 known plugins."""
    linuxdeploy = LinuxDeploy(mock_command)

    assert linuxdeploy.plugins == {
        "gtk": LinuxDeployGtkPlugin,
        "qt": LinuxDeployQtPlugin,
    }
