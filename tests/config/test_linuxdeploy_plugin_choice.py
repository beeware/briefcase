from pathlib import Path

import pytest

from briefcase.config import AppConfig, LinuxDeployPluginType


@pytest.mark.parametrize(
    "linuxdeploy_plugin,linuxdeploy_plugin_info",
    [
        (["gtk"], LinuxDeployPluginType.GTK),
        (
            ["https://briefcase.org/linuxdeploy-gtk-plugin.sh"],
            LinuxDeployPluginType.URL,
        ),
        (
            ["DEPLOY_GTK_VERSION=3 https://briefcase.org/linuxdeploy-gtk-plugin.sh"],
            LinuxDeployPluginType.URL,
        ),
    ],
)
def test_linuxdeploy_plugin_type_gtk_and_url(
    linuxdeploy_plugin, linuxdeploy_plugin_info
):
    """A simple config can be defined."""
    config = AppConfig(
        app_name="myapp",
        version="1.2.3",
        bundle="org.beeware",
        description="A simple app",
        sources=["src/myapp", "somewhere/else/interesting"],
        linuxdeploy_plugins=linuxdeploy_plugin,
    )
    assert config.linuxdeploy_plugins_info[0][0] == linuxdeploy_plugin_info


def test_linuxdeploy_plugin_type_file(tmpdir):
    """A simple config can be defined."""
    file_plugin = Path(tmpdir) / "linuxdeploy-gtk-plugin.sh"
    file_plugin.touch()
    config = AppConfig(
        app_name="myapp",
        version="1.2.3",
        bundle="org.beeware",
        description="A simple app",
        sources=["src/myapp", "somewhere/else/interesting"],
        linuxdeploy_plugins=[str(file_plugin)],
    )
    assert config.linuxdeploy_plugins_info[0][0] == LinuxDeployPluginType.FILE
