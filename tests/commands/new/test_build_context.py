from unittest.mock import MagicMock

import pytest

import briefcase.commands.new
from briefcase.bootstraps import (
    ConsoleBootstrap,
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


def test_question_sequence_toga(new_command):
    """Questions are asked, a context is constructed."""

    # Prime answers for all the questions.
    new_command.input.values = [
        "My Application",  # formal name
        "",  # app name - accept the default
        "org.beeware",  # bundle ID
        "My Project",  # project name
        "Cool stuff",  # description
        "Grace Hopper",  # author
        "grace@navy.mil",  # author email
        "https://navy.mil/myapplication",  # URL
        "4",  # license
        "1",  # Toga GUI toolkit
    ]

    context = new_command.build_context(
        project_overrides={},
    )

    assert context == dict(
        app_name="myapplication",
        author="Grace Hopper",
        author_email="grace@navy.mil",
        bundle="org.beeware",
        class_name="MyApplication",
        description="Cool stuff",
        formal_name="My Application",
        license="GNU General Public License v2 (GPLv2)",
        module_name="myapplication",
        source_dir="src/myapplication",
        test_source_dir="tests",
        project_name="My Project",
        url="https://navy.mil/myapplication",
        app_source='''\
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
        app_start_source="""\
from {{ cookiecutter.module_name }}.app import main

if __name__ == "__main__":
    main().main_loop()
""",
        pyproject_table_briefcase_app_extra_content="""
requires = [
]
test_requires = [
{% if cookiecutter.test_framework == "pytest" %}
    "pytest",
{% endif %}
]
""",
        pyproject_table_macOS="""\
universal_build = true
requires = [
    "toga-cocoa~=0.4.0",
    "std-nslog~=1.0.0",
]
""",
        pyproject_table_linux="""\
requires = [
    "toga-gtk~=0.4.0",
]
""",
        pyproject_table_linux_system_debian="""\
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
""",
        pyproject_table_linux_system_rhel="""\
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
        pyproject_table_linux_system_suse="""\
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
        pyproject_table_linux_system_arch="""\
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
        pyproject_table_linux_appimage="""\
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
        pyproject_table_linux_flatpak="""\
flatpak_runtime = "org.gnome.Platform"
flatpak_runtime_version = "45"
flatpak_sdk = "org.gnome.Sdk"
""",
        pyproject_table_windows="""\
requires = [
    "toga-winforms~=0.4.0",
]
""",
        pyproject_table_iOS="""\
requires = [
    "toga-iOS~=0.4.0",
    "std-nslog~=1.0.0",
]
""",
        pyproject_table_android="""\
requires = [
    "toga-android~=0.4.0",
]

base_theme = "Theme.MaterialComponents.Light.DarkActionBar"

build_gradle_dependencies = [
    "androidx.appcompat:appcompat:1.6.1",
    "com.google.android.material:material:1.11.0",
    # Needed for DetailedList
    "androidx.swiperefreshlayout:swiperefreshlayout:1.1.0",
]
""",
        pyproject_table_web="""\
requires = [
    "toga-web~=0.4.0",
]
style_framework = "Shoelace v2.3"
""",
    )


def test_question_sequence_console(new_command):
    """A console app can be constructed."""

    # Prime answers for all the questions.
    new_command.input.values = [
        "My Application",  # formal name
        "",  # app name - accept the default
        "org.beeware",  # bundle ID
        "My Project",  # project name
        "Cool stuff",  # description
        "Grace Hopper",  # author
        "grace@navy.mil",  # author email
        "https://navy.mil/myapplication",  # URL
        "4",  # license
        "4",  # Console app
    ]

    context = new_command.build_context(
        project_overrides={},
    )

    assert context == dict(
        app_name="myapplication",
        author="Grace Hopper",
        author_email="grace@navy.mil",
        bundle="org.beeware",
        class_name="MyApplication",
        description="Cool stuff",
        formal_name="My Application",
        license="GNU General Public License v2 (GPLv2)",
        module_name="myapplication",
        source_dir="src/myapplication",
        test_source_dir="tests",
        project_name="My Project",
        url="https://navy.mil/myapplication",
        app_source="""\

def main():
    # Your app logic goes here
    print("Hello, World.")

""",
        app_start_source="""\
from {{ cookiecutter.module_name }}.app import main

if __name__ == "__main__":
    main()
""",
        pyproject_table_briefcase_app_extra_content="""
console_app = true
requires = [
]
test_requires = [
{% if cookiecutter.test_framework == "pytest" %}
    "pytest",
{% endif %}
]
""",
        pyproject_table_macOS="""\
universal_build = true
requires = [
]
""",
        pyproject_table_linux="""\
requires = [
]
""",
        pyproject_table_linux_system_debian="""\
system_requires = [
    # Add any system packages needed at build the app here
]

system_runtime_requires = [
    # Add any system packages needed at runtime here
]
""",
        pyproject_table_linux_system_rhel="""\
system_requires = [
    # Add any system packages needed at build the app here
]

system_runtime_requires = [
    # Add any system packages needed at runtime here
]
""",
        pyproject_table_linux_system_suse="""\
system_requires = [
    # Add any system packages needed at build the app here
]

system_runtime_requires = [
    # Add any system packages needed at runtime here
]
""",
        pyproject_table_linux_system_arch="""\
system_requires = [
    # Add any system packages needed at build the app here
]

system_runtime_requires = [
    # Add any system packages needed at runtime here
]
""",
        pyproject_table_linux_flatpak="""\
flatpak_runtime = "org.freedesktop.Platform"
flatpak_runtime_version = "23.08"
flatpak_sdk = "org.freedesktop.Sdk"
""",
        pyproject_table_windows="""\
requires = [
]
""",
        pyproject_table_iOS="""\
supported = false
""",
        pyproject_table_android="""\
supported = false
""",
        pyproject_table_web="""\
supported = false
""",
    )


def test_question_sequence_pyside6(new_command):
    """Questions are asked, a context is constructed."""

    # Prime answers for all the questions.
    new_command.input.values = [
        "My Application",  # formal name
        "",  # app name - accept the default
        "org.beeware",  # bundle ID
        "My Project",  # project name
        "Cool stuff",  # description
        "Grace Hopper",  # author
        "grace@navy.mil",  # author email
        "https://navy.mil/myapplication",  # URL
        "4",  # license
        "2",  # PySide6 GUI toolkit
    ]

    context = new_command.build_context(
        project_overrides={},
    )

    assert context == dict(
        app_name="myapplication",
        author="Grace Hopper",
        author_email="grace@navy.mil",
        bundle="org.beeware",
        class_name="MyApplication",
        description="Cool stuff",
        formal_name="My Application",
        license="GNU General Public License v2 (GPLv2)",
        module_name="myapplication",
        source_dir="src/myapplication",
        test_source_dir="tests",
        project_name="My Project",
        url="https://navy.mil/myapplication",
        app_source="""\
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
        pyproject_table_briefcase_app_extra_content="""
requires = [
    "PySide6-Essentials~=6.5",
    # "PySide6-Addons~=6.5",
]
test_requires = [
{% if cookiecutter.test_framework == "pytest" %}
    "pytest",
{% endif %}
]
""",
        pyproject_table_macOS="""\
universal_build = true
requires = [
    "std-nslog~=1.0.0",
]
""",
        pyproject_table_linux="""\
requires = [
]
""",
        pyproject_table_linux_system_debian="""\
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
        pyproject_table_linux_system_rhel="""\
system_requires = [
]

system_runtime_requires = [
    "qt6-qtbase-gui",
]
""",
        pyproject_table_linux_system_suse="""\
system_requires = [
]

system_runtime_requires = [
    "libgthread-2_0-0",
    "libQt6Gui6",
]
""",
        pyproject_table_linux_system_arch="""\
system_requires = [
]

system_runtime_requires = [
    "qt6-base",
]
""",
        pyproject_table_linux_appimage="""\
manylinux = "manylinux_2_28"

system_requires = [
# ?? FIXME
]

linuxdeploy_plugins = [
]
""",
        pyproject_table_linux_flatpak="""\
flatpak_runtime = "org.kde.Platform"
flatpak_runtime_version = "6.6"
flatpak_sdk = "org.kde.Sdk"
""",
        pyproject_table_windows="""\
requires = [
]
""",
        pyproject_table_iOS="""\
supported = false
""",
        pyproject_table_android="""\
supported = false
""",
        pyproject_table_web="""\
supported = false
""",
    )


def test_question_sequence_pygame(new_command):
    """Questions are asked, a context is constructed."""

    # Prime answers for all the questions.
    new_command.input.values = [
        "My Application",  # formal name
        "",  # app name - accept the default
        "org.beeware",  # bundle ID
        "My Project",  # project name
        "Cool stuff",  # description
        "Grace Hopper",  # author
        "grace@navy.mil",  # author email
        "https://navy.mil/myapplication",  # URL
        "4",  # license
        "3",  # Pygame GUI toolkit
    ]

    context = new_command.build_context(
        project_overrides={},
    )

    assert context == dict(
        app_name="myapplication",
        author="Grace Hopper",
        author_email="grace@navy.mil",
        bundle="org.beeware",
        class_name="MyApplication",
        description="Cool stuff",
        formal_name="My Application",
        license="GNU General Public License v2 (GPLv2)",
        module_name="myapplication",
        source_dir="src/myapplication",
        test_source_dir="tests",
        project_name="My Project",
        url="https://navy.mil/myapplication",
        app_source="""\
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
        pyproject_table_briefcase_app_extra_content="""
requires = [
    "pygame~=2.2",
]
test_requires = [
{% if cookiecutter.test_framework == "pytest" %}
    "pytest",
{% endif %}
]
""",
        pyproject_table_macOS="""\
universal_build = true
requires = [
    "std-nslog~=1.0.0",
]
""",
        pyproject_table_linux="""\
requires = [
]
""",
        pyproject_table_linux_system_debian="""\
system_requires = [
]

system_runtime_requires = [
]
""",
        pyproject_table_linux_system_rhel="""\
system_requires = [
]

system_runtime_requires = [
]
""",
        pyproject_table_linux_system_suse="""\
system_requires = [
]

system_runtime_requires = [
]
""",
        pyproject_table_linux_system_arch="""\
system_requires = [
]

system_runtime_requires = [
]
""",
        pyproject_table_linux_appimage="""\
manylinux = "manylinux_2_28"

system_requires = [
]

linuxdeploy_plugins = [
]
""",
        pyproject_table_linux_flatpak="""\
flatpak_runtime = "org.freedesktop.Platform"
flatpak_runtime_version = "23.08"
flatpak_sdk = "org.freedesktop.Sdk"
""",
        pyproject_table_windows="""\
requires = [
]
""",
        pyproject_table_iOS="""\
supported = false
""",
        pyproject_table_android="""\
supported = false
""",
        pyproject_table_web="""\
supported = false
""",
    )


def test_question_sequence_none(new_command):
    """Questions are asked, a context is constructed."""

    # Prime answers for all the questions.
    new_command.input.values = [
        "My Application",  # formal name
        "",  # app name - accept the default
        "org.beeware",  # bundle ID
        "My Project",  # project name
        "Cool stuff",  # description
        "Grace Hopper",  # author
        "grace@navy.mil",  # author email
        "https://navy.mil/myapplication",  # URL
        "4",  # license
        "5",  # None
    ]

    context = new_command.build_context(
        project_overrides={},
    )

    assert context == dict(
        app_name="myapplication",
        author="Grace Hopper",
        author_email="grace@navy.mil",
        bundle="org.beeware",
        class_name="MyApplication",
        description="Cool stuff",
        formal_name="My Application",
        license="GNU General Public License v2 (GPLv2)",
        module_name="myapplication",
        source_dir="src/myapplication",
        test_source_dir="tests",
        project_name="My Project",
        url="https://navy.mil/myapplication",
    )


def test_question_sequence_with_overrides(
    new_command,
    mock_builtin_bootstraps,
    monkeypatch,
):
    """Questions are asked, a context is constructed."""

    # Prime answers for none of the questions.
    new_command.input.values = []

    class GuiBootstrap:
        fields = []

        def __init__(self, context):
            pass

    monkeypatch.setattr(
        briefcase.commands.new,
        "get_gui_bootstraps",
        MagicMock(
            return_value=dict(
                **mock_builtin_bootstraps,
                **{"Custom GUI": GuiBootstrap},
            ),
        ),
    )

    context = new_command.build_context(
        project_overrides=dict(
            formal_name="My Override App",
            app_name="myoverrideapp",
            bundle="net.example",
            project_name="My Override Project",
            description="My override description",
            author="override, author",
            author_email="author@override.tld",
            url="https://override.example.com",
            license="MIT license",
            bootstrap="Custom GUI",
        ),
    )

    assert context == dict(
        app_name="myoverrideapp",
        author="override, author",
        author_email="author@override.tld",
        bundle="net.example",
        class_name="MyOverrideApp",
        description="My override description",
        formal_name="My Override App",
        license="MIT license",
        module_name="myoverrideapp",
        source_dir="src/myoverrideapp",
        test_source_dir="tests",
        project_name="My Override Project",
        url="https://override.example.com",
    )


def test_question_sequence_with_bad_license_override(
    new_command,
    mock_builtin_bootstraps,
    monkeypatch,
):
    """A bad override for license uses user input instead."""

    # Prime answers for all the questions.
    new_command.input.values = [
        "4",  # license
    ]

    class GuiBootstrap:
        fields = []

        def __init__(self, context):
            pass

    monkeypatch.setattr(
        briefcase.commands.new,
        "get_gui_bootstraps",
        MagicMock(
            return_value=dict(
                **mock_builtin_bootstraps,
                **{"Custom GUI": GuiBootstrap},
            ),
        ),
    )

    context = new_command.build_context(
        project_overrides=dict(
            formal_name="My Override App",
            app_name="myoverrideapp",
            bundle="net.example",
            project_name="My Override Project",
            description="My override description",
            author="override, author",
            author_email="author@override.tld",
            url="https://override.example.com",
            license="BAD i don't exist license",
            bootstrap="Custom GUI",
        ),
    )

    assert context == dict(
        app_name="myoverrideapp",
        author="override, author",
        author_email="author@override.tld",
        bundle="net.example",
        class_name="MyOverrideApp",
        description="My override description",
        formal_name="My Override App",
        license="GNU General Public License v2 (GPLv2)",
        module_name="myoverrideapp",
        source_dir="src/myoverrideapp",
        test_source_dir="tests",
        project_name="My Override Project",
        url="https://override.example.com",
    )


def test_question_sequence_with_bad_bootstrap_override(
    new_command,
    mock_builtin_bootstraps,
    monkeypatch,
):
    """A bad override for the bootstrap uses user input instead."""

    # Prime answers for none of the questions.
    new_command.input.values = [
        "6",  # None
    ]

    class GuiBootstrap:
        # if this custom bootstrap is chosen, the lack of
        # requires() would cause an error
        fields = ["requires"]

        def __init__(self, context):
            pass

    monkeypatch.setattr(
        briefcase.commands.new,
        "get_gui_bootstraps",
        MagicMock(
            return_value=dict(
                **mock_builtin_bootstraps,
                **{"Custom GUI": GuiBootstrap},
            ),
        ),
    )

    context = new_command.build_context(
        project_overrides=dict(
            formal_name="My Override App",
            app_name="myoverrideapp",
            bundle="net.example",
            project_name="My Override Project",
            description="My override description",
            author="override, author",
            author_email="author@override.tld",
            url="https://override.example.com",
            license="MIT license",
            bootstrap="BAD i don't exist GUI",
        ),
    )

    assert context == dict(
        app_name="myoverrideapp",
        author="override, author",
        author_email="author@override.tld",
        bundle="net.example",
        class_name="MyOverrideApp",
        description="My override description",
        formal_name="My Override App",
        license="MIT license",
        module_name="myoverrideapp",
        source_dir="src/myoverrideapp",
        test_source_dir="tests",
        project_name="My Override Project",
        url="https://override.example.com",
    )


def test_question_sequence_with_no_user_input(new_command):
    """If no user input is provided, all user inputs are taken as default."""

    new_command.input.enabled = False

    context = new_command.build_context(project_overrides={})

    assert context == dict(
        app_name="helloworld",
        author="Jane Developer",
        author_email="jane@example.com",
        bundle="com.example",
        class_name="HelloWorld",
        description="My first application",
        formal_name="Hello World",
        license="BSD license",
        module_name="helloworld",
        source_dir="src/helloworld",
        test_source_dir="tests",
        project_name="Hello World",
        url="https://example.com/helloworld",
        app_source='''\
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
        app_start_source="""\
from {{ cookiecutter.module_name }}.app import main

if __name__ == "__main__":
    main().main_loop()
""",
        pyproject_table_briefcase_app_extra_content="""
requires = [
]
test_requires = [
{% if cookiecutter.test_framework == "pytest" %}
    "pytest",
{% endif %}
]
""",
        pyproject_table_macOS="""\
universal_build = true
requires = [
    "toga-cocoa~=0.4.0",
    "std-nslog~=1.0.0",
]
""",
        pyproject_table_linux="""\
requires = [
    "toga-gtk~=0.4.0",
]
""",
        pyproject_table_linux_system_debian="""\
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
""",
        pyproject_table_linux_system_rhel="""\
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
        pyproject_table_linux_system_suse="""\
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
        pyproject_table_linux_system_arch="""\
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
        pyproject_table_linux_appimage="""\
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
        pyproject_table_linux_flatpak="""\
flatpak_runtime = "org.gnome.Platform"
flatpak_runtime_version = "45"
flatpak_sdk = "org.gnome.Sdk"
""",
        pyproject_table_windows="""\
requires = [
    "toga-winforms~=0.4.0",
]
""",
        pyproject_table_iOS="""\
requires = [
    "toga-iOS~=0.4.0",
    "std-nslog~=1.0.0",
]
""",
        pyproject_table_android="""\
requires = [
    "toga-android~=0.4.0",
]

base_theme = "Theme.MaterialComponents.Light.DarkActionBar"

build_gradle_dependencies = [
    "androidx.appcompat:appcompat:1.6.1",
    "com.google.android.material:material:1.11.0",
    # Needed for DetailedList
    "androidx.swiperefreshlayout:swiperefreshlayout:1.1.0",
]
""",
        pyproject_table_web="""\
requires = [
    "toga-web~=0.4.0",
]
style_framework = "Shoelace v2.3"
""",
    )


def test_question_sequence_custom_bootstrap(
    new_command,
    mock_builtin_bootstraps,
    monkeypatch,
):
    """Questions are asked, a context is constructed."""

    class GuiBootstrap:
        fields = ["requires", "platform"]

        def __init__(self, context):
            pass

        def extra_context(self):
            return {"custom_context": "value"}

        def requires(self):
            return "toga"

        def platform(self):
            return "bsd"

    monkeypatch.setattr(
        briefcase.commands.new,
        "get_gui_bootstraps",
        MagicMock(
            return_value=dict(
                **mock_builtin_bootstraps,
                **{"Custom GUI": GuiBootstrap},
            ),
        ),
    )

    # Prime answers for all the questions.
    new_command.input.values = [
        "My Application",  # formal name
        "",  # app name - accept the default
        "org.beeware",  # bundle ID
        "My Project",  # project name
        "Cool stuff",  # description
        "Grace Hopper",  # author
        "grace@navy.mil",  # author email
        "https://navy.mil/myapplication",  # URL
        "4",  # license
        "5",  # Custom GUI bootstrap
    ]

    context = new_command.build_context(project_overrides={})

    assert context == dict(
        app_name="myapplication",
        author="Grace Hopper",
        author_email="grace@navy.mil",
        bundle="org.beeware",
        class_name="MyApplication",
        description="Cool stuff",
        formal_name="My Application",
        license="GNU General Public License v2 (GPLv2)",
        module_name="myapplication",
        source_dir="src/myapplication",
        test_source_dir="tests",
        project_name="My Project",
        url="https://navy.mil/myapplication",
        custom_context="value",
        requires="toga",
        platform="bsd",
    )


def test_question_sequence_custom_bootstrap_without_additional_context(
    new_command,
    mock_builtin_bootstraps,
    monkeypatch,
):
    """Questions are asked, a context is constructed."""

    class GuiBootstrap:
        fields = ["requires", "platform"]

        def __init__(self, context):
            pass

        def requires(self):
            return "toga"

        def platform(self):
            return "bsd"

    monkeypatch.setattr(
        briefcase.commands.new,
        "get_gui_bootstraps",
        MagicMock(
            return_value=dict(
                **mock_builtin_bootstraps,
                **{"Custom GUI": GuiBootstrap},
            ),
        ),
    )

    # Prime answers for all the questions.
    new_command.input.values = [
        "My Application",  # formal name
        "",  # app name - accept the default
        "org.beeware",  # bundle ID
        "My Project",  # project name
        "Cool stuff",  # description
        "Grace Hopper",  # author
        "grace@navy.mil",  # author email
        "https://navy.mil/myapplication",  # URL
        "4",  # license
        "5",  # Custom GUI bootstrap
    ]

    context = new_command.build_context(project_overrides={})

    assert context == dict(
        app_name="myapplication",
        author="Grace Hopper",
        author_email="grace@navy.mil",
        bundle="org.beeware",
        class_name="MyApplication",
        description="Cool stuff",
        formal_name="My Application",
        license="GNU General Public License v2 (GPLv2)",
        module_name="myapplication",
        source_dir="src/myapplication",
        test_source_dir="tests",
        project_name="My Project",
        url="https://navy.mil/myapplication",
        requires="toga",
        platform="bsd",
    )
