from briefcase.bootstraps.base import BaseGuiBootstrap


class PursuedPyBearGuiBootstrap(BaseGuiBootstrap):
    def app_source(self):
        return """\
import importlib.metadata
import os
import sys

import ppb


class {{ cookiecutter.class_name }}(ppb.Scene):
    def __init__(self, **props):
        super().__init__(**props)

        self.add(
            ppb.Sprite(
                image=ppb.Image("{{ cookiecutter.module_name }}/resources/{{ cookiecutter.app_name }}.png"),
            )
        )


def main():
    # Linux desktop environments use app's .desktop file to integrate the app
    # to their application menus. The .desktop file of this app will include
    # StartupWMClass key, set to app's formal name, which helps associate
    # app's windows to its menu item.
    #
    # For association to work any windows of the app must have WMCLASS
    # property set to match the value set in app's desktop file. For PPB this
    # is set using environment variable.

    # Find the name of the module that was used to start the app
    app_module = sys.modules["__main__"].__package__
    # Retrieve the app's metadata
    metadata = importlib.metadata.metadata(app_module)

    os.environ["SDL_VIDEO_X11_WMCLASS"] = metadata["Formal-Name"]

    ppb.run(
        starting_scene={{ cookiecutter.class_name }},
        title=metadata["Formal-Name"],
    )
"""

    def pyproject_table_briefcase_app_extra_content(self):
        return """

requires = [
    "ppb~=1.1",
]
test_requires = [
{%- if cookiecutter.test_framework == "pytest" %}
    "pytest",
{%- endif %}
]
"""

    def pyproject_table_macOS(self):
        return """
universal_build = true
requires = [
    "std-nslog~=1.0.0",
]
"""

    def pyproject_table_linux(self):
        return """
requires = [
]
"""

    def pyproject_table_linux_system_debian(self):
        return """
system_requires = [
# ?? FIXME
]

system_runtime_requires = [
# ?? FIXME
]
"""

    def pyproject_table_linux_system_rhel(self):
        return """
system_requires = [
# ?? FIXME
]

system_runtime_requires = [
# ?? FIXME
]
"""

    def pyproject_table_linux_system_suse(self):
        return """
system_requires = [
# ?? FIXME
]

system_runtime_requires = [
# ?? FIXME
]
"""

    def pyproject_table_linux_system_arch(self):
        return """
system_requires = [
# ?? FIXME
]

system_runtime_requires = [
# ?? FIXME
]
"""

    def pyproject_table_linux_appimage(self):
        return """
manylinux = "manylinux2014"

system_requires = [
# ?? FIXME
]

linuxdeploy_plugins = [
]
"""

    def pyproject_table_linux_flatpak(self):
        return """
flatpak_runtime = "org.freedesktop.Platform"
flatpak_runtime_version = "22.08"
flatpak_sdk = "org.freedesktop.Sdk"
"""

    def pyproject_table_windows(self):
        return """
requires = [
]
"""

    def pyproject_table_iOS(self):
        return """
supported = false
"""

    def pyproject_table_android(self):
        return """
supported = false
"""

    def pyproject_table_web(self):
        return """
supported = false
"""
