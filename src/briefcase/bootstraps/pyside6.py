from briefcase.bootstraps.base import BaseGuiBootstrap


class PySide6GuiBootstrap(BaseGuiBootstrap):
    display_name_annotation = "does not support iOS/Android/Web deployment"

    def app_source(self):
        return """\
import importlib.metadata
import sys

from PySide6 import QtWidgets


class {{ cookiecutter.class_name }}(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("{{ cookiecutter.app_name }}")
        self.show()


def main():
    # Linux desktop environments use an app's .desktop file to integrate the app
    # in to their application menus. The .desktop file of this app will include
    # the StartupWMClass key, set to app's formal name. This helps associate the
    # app's windows to its menu item.
    #
    # For association to work, any windows of the app must have WMCLASS property
    # set to match the value set in app's desktop file. For PySide6, this is set
    # with setApplicationName().

    # Find the name of the module that was used to start the app
    app_module = sys.modules["__main__"].__package__
    # Retrieve the app's metadata
    metadata = importlib.metadata.metadata(app_module)

    QtWidgets.QApplication.setApplicationName(metadata["Formal-Name"])

    app = QtWidgets.QApplication(sys.argv)
    main_window = {{ cookiecutter.class_name }}()
    sys.exit(app.exec())
"""

    def pyproject_table_briefcase_app_extra_content(self):
        return """
requires = [
    "PySide6-Essentials~=6.7",
    # "PySide6-Addons~=6.7",
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
    "std-nslog~=1.0.3",
]
"""

    def pyproject_table_linux(self):
        return """\
requires = [
]
"""

    def pyproject_table_linux_system_debian(self):
        return """\
system_requires = [
]

system_runtime_requires = [
    # Derived from https://doc.qt.io/qt-6/linux-requirements.html
    "libxext6",
    "libxrender1",
    "libx11-xcb1",
    "libxkbcommon-x11-0",
    "libxcb-image0",
    "libxcb-cursor0",
    "libxcb-shape0",
    "libxcb-randr0",
    "libxcb-xfixes0",
    "libxcb-sync1",
    "libxcb-icccm4",
    "libxcb-keysyms1",
    "libfontconfig1",
    "libsm6",
    "libice6",
    "libglib2.0-0",
    "libgl1",
    "libegl1",
    "libdbus-1-3",
]
"""

    def pyproject_table_linux_system_rhel(self):
        return """\
system_requires = [
]

system_runtime_requires = [
    "qt6-qtbase-gui",
]
"""

    def pyproject_table_linux_system_suse(self):
        return """\
system_requires = [
]

system_runtime_requires = [
    "libgthread-2_0-0",
    "libQt6Gui6",
]
"""

    def pyproject_table_linux_system_arch(self):
        return """\
system_requires = [
]

system_runtime_requires = [
    "qt6-base",
]
"""

    def pyproject_table_linux_appimage(self):
        return """\
manylinux = "manylinux_2_28"

system_requires = [
# ?? FIXME
]

linuxdeploy_plugins = [
]
"""

    def pyproject_table_linux_flatpak(self):
        return """\
flatpak_runtime = "org.kde.Platform"
flatpak_runtime_version = "6.7"
flatpak_sdk = "org.kde.Sdk"
"""

    def pyproject_table_windows(self):
        return """\
requires = [
]
"""

    def pyproject_table_iOS(self):
        return """\
supported = false
"""

    def pyproject_table_android(self):
        return """\
supported = false
"""

    def pyproject_table_web(self):
        return """\
supported = false
"""
