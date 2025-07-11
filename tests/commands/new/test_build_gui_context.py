from unittest.mock import MagicMock

import pytest

import briefcase.commands.new
from briefcase.bootstraps import (
    ConsoleBootstrap,
    EmptyBootstrap,
    PygameGuiBootstrap,
    PySide6GuiBootstrap,
    TogaGuiBootstrap,
)


@pytest.fixture
def mock_builtin_bootstraps():
    return {
        "Toga": TogaGuiBootstrap,
        "Console": ConsoleBootstrap,
        "PySide6": PySide6GuiBootstrap,
        "Pygame": PygameGuiBootstrap,
    }


def test_toga_bootstrap(new_command):
    """Context can be requested from the Toga bootstrap."""

    context = new_command.build_gui_context(
        TogaGuiBootstrap(
            new_command.console,
            {
                "app_name": "myapplication",
                "author": "Grace Hopper",
            },
        ),
        project_overrides={},
    )

    assert context == {
        "app_source": '''\
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
''',
        "app_start_source": """\
from {{ cookiecutter.module_name }}.app import main

if __name__ == "__main__":
    main().main_loop()
""",
        "pyproject_table_briefcase_app_extra_content": """
requires = [
]
test_requires = [
{% if cookiecutter.test_framework == "pytest" %}
    "pytest",
{% endif %}
]
""",
        "pyproject_table_macOS": """\
universal_build = true
requires = [
    "toga-cocoa~=0.5.0",
    "std-nslog~=1.0.3",
]
""",
        "pyproject_table_linux": """\
requires = [
    "toga-gtk~=0.5.0",
    # PyGObject 3.52.1 enforces a requirement on libgirepository-2.0-dev. This library
    # isn't available on Debian 12/Ubuntu 22.04. If you don't need to support those (or
    # older) releases, you can remove this version pin. See beeware/toga#3143.
    "pygobject < 3.52.1",
]
""",
        "pyproject_table_linux_system_debian": """\
system_requires = [
    # Needed to compile pycairo wheel
    "libcairo2-dev",
    # One of the following two packages are needed to compile PyGObject wheel. If you
    # remove the pygobject pin in the requires list, you should also change to the
    # version 2.0 of the girepository library. See beeware/toga#3143.
    "libgirepository1.0-dev",
    # "libgirepository-2.0-dev",
]

system_runtime_requires = [
    # Needed to provide GTK and its GI bindings
    "gir1.2-gtk-3.0",
    # One of the following two packages are needed to use PyGObject at runtime. If you
    # remove the pygobject pin in the requires list, you should also change to the
    # version 2.0 of the girepository library. See beeware/toga#3143.
    "libgirepository-1.0-1",
    # "libgirepository-2.0-0",
    # Dependencies that GTK looks for at runtime
    "libcanberra-gtk3-module",
    # Needed to provide WebKit2 at runtime
    # Note: Debian 11 requires gir1.2-webkit2-4.0 instead
    # "gir1.2-webkit2-4.1",
]
""",
        "pyproject_table_linux_system_rhel": """\
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
""",
        "pyproject_table_linux_system_suse": """\
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
""",
        "pyproject_table_linux_system_arch": """\
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
""",
        "pyproject_table_linux_appimage": """\
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
""",
        "pyproject_table_linux_flatpak": """\
flatpak_runtime = "org.gnome.Platform"
flatpak_runtime_version = "48"
flatpak_sdk = "org.gnome.Sdk"
""",
        "pyproject_table_windows": """\
requires = [
    "toga-winforms~=0.5.0",
]
""",
        "pyproject_table_iOS": """\
requires = [
    "toga-iOS~=0.5.0",
    "std-nslog~=1.0.3",
]
""",
        "pyproject_table_android": """\
requires = [
    "toga-android~=0.5.0",
]

base_theme = "Theme.MaterialComponents.Light.DarkActionBar"

build_gradle_dependencies = [
    "com.google.android.material:material:1.12.0",
    # Needed for DetailedList
    # "androidx.swiperefreshlayout:swiperefreshlayout:1.1.0",
    # Needed for MapView
    # "org.osmdroid:osmdroid-android:6.1.20",
]
""",
        "pyproject_table_web": """\
requires = [
    "toga-web~=0.5.0",
]
style_framework = "Shoelace v2.3"
""",
    }


def test_console_bootstrap(new_command):
    """Context can be requested from the Console bootstrap."""

    context = new_command.build_gui_context(
        ConsoleBootstrap(
            new_command.console,
            {
                "app_name": "myapplication",
                "author": "Grace Hopper",
            },
        ),
        project_overrides={},
    )

    assert context == {
        "console_app": True,
        "app_source": """\

def main():
    # Your app logic goes here
    print("Hello, World.")
""",
        "app_start_source": """\
from {{ cookiecutter.module_name }}.app import main

if __name__ == "__main__":
    main()
""",
        "pyproject_table_briefcase_app_extra_content": """
requires = [
    # Add your cross-platform app requirements here
]
test_requires = [
{% if cookiecutter.test_framework == "pytest" %}
    "pytest",
{% endif %}
]
""",
        "pyproject_table_macOS": """\
universal_build = true
requires = [
    # Add your macOS-specific app requirements here
]
""",
        "pyproject_table_linux": """\
requires = [
    # Add your Linux-specific app requirements here
]
""",
        "pyproject_table_linux_system_debian": """\
system_requires = [
    # Add any system packages needed at build the app here
]

system_runtime_requires = [
    # Add any system packages needed at runtime here
]
""",
        "pyproject_table_linux_system_rhel": """\
system_requires = [
    # Add any system packages needed at build the app here
]

system_runtime_requires = [
    # Add any system packages needed at runtime here
]
""",
        "pyproject_table_linux_system_suse": """\
system_requires = [
    # Add any system packages needed at build the app here
]

system_runtime_requires = [
    # Add any system packages needed at runtime here
]
""",
        "pyproject_table_linux_system_arch": """\
system_requires = [
    # Add any system packages needed at build the app here
]

system_runtime_requires = [
    # Add any system packages needed at runtime here
]
""",
        "pyproject_table_linux_flatpak": """\
flatpak_runtime = "org.freedesktop.Platform"
flatpak_runtime_version = "24.08"
flatpak_sdk = "org.freedesktop.Sdk"
""",
        "pyproject_table_windows": """\
requires = [
    # Add your Windows-specific app requirements here
]
""",
        "pyproject_table_iOS": """\
supported = false
""",
        "pyproject_table_android": """\
supported = false
""",
        "pyproject_table_web": """\
supported = false
""",
    }


def test_pyside6_bootstrap(new_command):
    """Context can be requested from the PySide6 bootstrap."""

    context = new_command.build_gui_context(
        PySide6GuiBootstrap(
            new_command.console,
            {
                "app_name": "myapplication",
                "author": "Grace Hopper",
            },
        ),
        project_overrides={},
    )

    assert context == {
        "app_source": """\
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
""",
        "pyproject_table_briefcase_app_extra_content": """
requires = [
    "PySide6-Essentials~=6.8",
    # "PySide6-Addons~=6.8",
]
test_requires = [
{% if cookiecutter.test_framework == "pytest" %}
    "pytest",
{% endif %}
]
""",
        "pyproject_table_macOS": """\
universal_build = true
# As of Pyside 6.8, PySide enforces a macOS 12 minimum on wheels.
min_os_version = "12.0"
requires = [
    "std-nslog~=1.0.3",
]
""",
        "pyproject_table_linux": """\
requires = [
]
""",
        "pyproject_table_linux_system_debian": """\
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
""",
        "pyproject_table_linux_system_rhel": """\
system_requires = [
]

system_runtime_requires = [
    "qt6-qtbase-gui",
]
""",
        "pyproject_table_linux_system_suse": """\
system_requires = [
]

system_runtime_requires = [
    "libgthread-2_0-0",
    "libQt6Gui6",
]
""",
        "pyproject_table_linux_system_arch": """\
system_requires = [
]

system_runtime_requires = [
    "qt6-base",
]
""",
        "pyproject_table_linux_appimage": """\
manylinux = "manylinux_2_28"

system_requires = [
# ?? FIXME
]

linuxdeploy_plugins = [
]
""",
        "pyproject_table_linux_flatpak": """\
flatpak_runtime = "org.kde.Platform"
flatpak_runtime_version = "6.9"
flatpak_sdk = "org.kde.Sdk"
""",
        "pyproject_table_windows": """\
requires = [
]
""",
        "pyproject_table_iOS": """\
supported = false
""",
        "pyproject_table_android": """\
supported = false
""",
        "pyproject_table_web": """\
supported = false
""",
    }


def test_pygame_bootstrap(new_command):
    """Context can be requested from the Pygame bootstrap."""

    context = new_command.build_gui_context(
        PygameGuiBootstrap(
            new_command.console,
            {
                "app_name": "myapplication",
                "author": "Grace Hopper",
            },
        ),
        project_overrides={},
    )

    assert context == {
        "app_source": """\
import importlib.metadata
import os
import sys
from pathlib import Path

import pygame


SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
WHITE = (255, 255, 255)


def main():
    # Linux desktop environments use an app's .desktop file to integrate the app
    # in to their application menus. The .desktop file of this app will include
    # the StartupWMClass key, set to app's formal name. This helps associate the
    # app's windows to its menu item.
    #
    # For association to work, any windows of the app must have WMCLASS property
    # set to match the value set in app's desktop file. For PyGame, this is set
    # using the SDL_VIDEO_X11_WMCLASS environment variable.

    # Find the name of the module that was used to start the app
    app_module = sys.modules["__main__"].__package__
    # Retrieve the app's metadata
    metadata = importlib.metadata.metadata(app_module)

    os.environ["SDL_VIDEO_X11_WMCLASS"] = metadata["Formal-Name"]

    pygame.init()
    pygame.display.set_caption(metadata["Formal-Name"])
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                break

        screen.fill(WHITE)
        pygame.display.flip()

    pygame.quit()
""",
        "pyproject_table_briefcase_app_extra_content": """
requires = [
    "pygame~=2.6",
]
test_requires = [
{% if cookiecutter.test_framework == "pytest" %}
    "pytest",
{% endif %}
]
""",
        "pyproject_table_macOS": """\
universal_build = true
requires = [
    "std-nslog~=1.0.3",
]
""",
        "pyproject_table_linux": """\
requires = [
]
""",
        "pyproject_table_linux_system_debian": """\
system_requires = [
]

system_runtime_requires = [
]
""",
        "pyproject_table_linux_system_rhel": """\
system_requires = [
]

system_runtime_requires = [
]
""",
        "pyproject_table_linux_system_suse": """\
system_requires = [
]

system_runtime_requires = [
]
""",
        "pyproject_table_linux_system_arch": """\
system_requires = [
]

system_runtime_requires = [
]
""",
        "pyproject_table_linux_appimage": """\
manylinux = "manylinux_2_28"

system_requires = [
]

linuxdeploy_plugins = [
]
""",
        "pyproject_table_linux_flatpak": """\
flatpak_runtime = "org.freedesktop.Platform"
flatpak_runtime_version = "24.08"
flatpak_sdk = "org.freedesktop.Sdk"
""",
        "pyproject_table_windows": """\
requires = [
]
""",
        "pyproject_table_iOS": """\
supported = false
""",
        "pyproject_table_android": """\
supported = false
""",
        "pyproject_table_web": """\
supported = false
""",
    }


def test_no_bootstrap(new_command):
    """The empty bootstrap is used if no bootstrap is selected."""

    context = new_command.build_gui_context(
        EmptyBootstrap(
            new_command.console,
            {
                "app_name": "myapplication",
                "author": "Grace Hopper",
            },
        ),
        project_overrides={},
    )

    assert context == {
        "app_source": """\

def main():
    # Your app logic goes here
    print("Hello, World.")
""",
        "app_start_source": """\
from {{ cookiecutter.module_name }}.app import main

if __name__ == "__main__":
    main()
""",
        "pyproject_table_briefcase_app_extra_content": """
requires = [
    # Add your cross-platform app requirements here
]
test_requires = [
    # Add your cross-platform test requirements here
]
""",
        "pyproject_table_macOS": """\
universal_build = true
requires = [
    # Add your macOS-specific app requirements here
]
""",
        "pyproject_table_linux": """\
requires = [
    # Add your Linux-specific app requirements here
]
""",
        "pyproject_table_linux_system_debian": """\
system_requires = [
    # Add any system packages needed at build the app here
]

system_runtime_requires = [
    # Add any system packages needed at runtime here
]
""",
        "pyproject_table_linux_system_rhel": """\
system_requires = [
    # Add any system packages needed at build the app here
]

system_runtime_requires = [
    # Add any system packages needed at runtime here
]
""",
        "pyproject_table_linux_system_suse": """\
system_requires = [
    # Add any system packages needed at build the app here
]

system_runtime_requires = [
    # Add any system packages needed at runtime here
]
""",
        "pyproject_table_linux_system_arch": """\
system_requires = [
    # Add any system packages needed at build the app here
]

system_runtime_requires = [
    # Add any system packages needed at runtime here
]
""",
        "pyproject_table_linux_flatpak": """\
flatpak_runtime = "org.freedesktop.Platform"
flatpak_runtime_version = "24.08"
flatpak_sdk = "org.freedesktop.Sdk"
""",
        "pyproject_table_windows": """\
requires = [
    # Add your Windows-specific app requirements here
]
""",
        "pyproject_table_iOS": """\
requires = [
    # Add your iOS-specific app requirements here
]
""",
        "pyproject_table_android": """\
requires = [
    # Add your Android-specific app requirements here
]
""",
        "pyproject_table_web": """\
requires = [
    # Add your web-specific app requirements here
]
""",
    }


def test_custom_bootstrap(
    new_command,
    mock_builtin_bootstraps,
    monkeypatch,
):
    """A context is create for a custom bootstrap."""

    class GuiBootstrap:
        fields = ["requires", "platform"]

        def __init__(self, console, context):
            self.console = console
            self.context = context

        def extra_context(self, project_overrides):
            return {
                "custom_context": "value",
                "custom_override": project_overrides.pop("custom_override", None),
            }

        def requires(self):
            return "toga"

        def platform(self):
            return "bsd"

    monkeypatch.setattr(
        briefcase.commands.new,
        "get_gui_bootstraps",
        MagicMock(
            return_value={
                **mock_builtin_bootstraps,
                **{"Custom GUI": GuiBootstrap},
            },
        ),
    )

    context = new_command.build_gui_context(
        GuiBootstrap(
            new_command.console,
            {
                "app_name": "myapplication",
                "author": "Grace Hopper",
            },
        ),
        project_overrides={"custom_override": "other"},
    )

    assert context == {
        "custom_context": "value",
        "custom_override": "other",
        "requires": "toga",
        "platform": "bsd",
    }
