from briefcase.bootstraps.base import BaseGuiBootstrap


class TogaGuiBootstrap(BaseGuiBootstrap):
    def app_source(self):
        return '''\
import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW


class {{ cookiecutter.class_name }}(toga.App):
    def startup(self):
        """Construct and show the Toga application.

        Usually, you would add your application to a main content box.
        We then create a main window (with a name matching the app), and
        show the main window.
        """
        main_box = toga.Box()

        self.main_window = toga.MainWindow(title=self.formal_name)
        self.main_window.content = main_box
        self.main_window.show()


def main():
    return {{ cookiecutter.class_name }}()
'''

    def app_start_source(self):
        return """\
from {{ cookiecutter.module_name }}.app import main

if __name__ == "__main__":
    main().main_loop()
"""

    def pyproject_table_briefcase_app_extra_content(self):
        return """
requires = [
]
test_requires = [
{% if cookiecutter.test_framework == "pytest" %}
    "pytest",
{% endif %}
]
"""

    def pyproject_table_macOS(self):
        return """\
universal_build = true
requires = [
    "toga-cocoa~=0.4.5",
    "std-nslog~=1.0.0",
]
"""

    def pyproject_table_linux(self):
        return """\
requires = [
    "toga-gtk~=0.4.5",
]
"""

    def pyproject_table_linux_system_debian(self):
        return """\
system_requires = [
    # Needed to compile pycairo wheel
    "libcairo2-dev",
    # Needed to compile PyGObject wheel
    "libgirepository1.0-dev",
]

system_runtime_requires = [
    # Needed to provide GTK and its GI bindings
    "gir1.2-gtk-3.0",
    "libgirepository-1.0-1",
    # Dependencies that GTK looks for at runtime
    "libcanberra-gtk3-module",
    # Needed to provide WebKit2 at runtime
    # Note: Debian 11 and Ubuntu 20.04 require gir1.2-webkit2-4.0 instead
    # "gir1.2-webkit2-4.1",
]
"""

    def pyproject_table_linux_system_rhel(self):
        return """\
system_requires = [
    # Needed to compile pycairo wheel
    "cairo-gobject-devel",
    # Needed to compile PyGObject wheel
    "gobject-introspection-devel",
]

system_runtime_requires = [
    # Needed to support Python bindings to GTK
    "gobject-introspection",
    # Needed to provide GTK
    "gtk3",
    # Dependencies that GTK looks for at runtime
    "libcanberra-gtk3",
    # Needed to provide WebKit2 at runtime
    # "webkit2gtk3",
]
"""

    def pyproject_table_linux_system_suse(self):
        return """\
system_requires = [
    # Needed to compile pycairo wheel
    "cairo-devel",
    # Needed to compile PyGObject wheel
    "gobject-introspection-devel",
]

system_runtime_requires = [
    # Needed to provide GTK
    "gtk3",
    # Needed to support Python bindings to GTK
    "gobject-introspection", "typelib(Gtk) = 3.0",
    # Dependencies that GTK looks for at runtime
    "libcanberra-gtk3-module",
    # Needed to provide WebKit2 at runtime
    # "libwebkit2gtk3", "typelib(WebKit2)",
]
"""

    def pyproject_table_linux_system_arch(self):
        return """\
system_requires = [
    # Needed to compile pycairo wheel
    "cairo",
    # Needed to compile PyGObject wheel
    "gobject-introspection",
    # Runtime dependencies that need to exist so that the
    # Arch package passes final validation.
    # Needed to provide GTK
    "gtk3",
    # Dependencies that GTK looks for at runtime
    "libcanberra",
    # Needed to provide WebKit2
    # "webkit2gtk",
]

system_runtime_requires = [
    # Needed to provide GTK
    "gtk3",
    # Needed to provide PyGObject bindings
    "gobject-introspection-runtime",
    # Dependencies that GTK looks for at runtime
    "libcanberra",
    # Needed to provide WebKit2 at runtime
    # "webkit2gtk",
]
"""

    def pyproject_table_linux_appimage(self):
        return """\
manylinux = "manylinux_2_28"

system_requires = [
    # Needed to compile pycairo wheel
    "cairo-gobject-devel",
    # Needed to compile PyGObject wheel
    "gobject-introspection-devel",
    # Needed to provide GTK
    "gtk3-devel",
    # Dependencies that GTK looks for at runtime, that need to be
    # in the build environment to be picked up by linuxdeploy
    "libcanberra-gtk3",
    "PackageKit-gtk3-module",
    "gvfs-client",
]

linuxdeploy_plugins = [
    "DEPLOY_GTK_VERSION=3 gtk",
]
"""

    def pyproject_table_linux_flatpak(self):
        return """\
flatpak_runtime = "org.gnome.Platform"
flatpak_runtime_version = "45"
flatpak_sdk = "org.gnome.Sdk"
"""

    def pyproject_table_windows(self):
        return """\
requires = [
    "toga-winforms~=0.4.5",
]
"""

    def pyproject_table_iOS(self):
        return """\
requires = [
    "toga-iOS~=0.4.5",
    "std-nslog~=1.0.0",
]
"""

    def pyproject_table_android(self):
        return """\
requires = [
    "toga-android~=0.4.5",
]

base_theme = "Theme.MaterialComponents.Light.DarkActionBar"

build_gradle_dependencies = [
    "com.google.android.material:material:1.11.0",
    # Needed for DetailedList
    # "androidx.swiperefreshlayout:swiperefreshlayout:1.1.0",
    # Needed for MapView
    # "org.osmdroid:osmdroid-android:6.1.0",
]
"""

    def pyproject_table_web(self):
        return """\
requires = [
    "toga-web~=0.4.5",
]
style_framework = "Shoelace v2.3"
"""
