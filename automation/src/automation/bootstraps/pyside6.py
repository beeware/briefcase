from automation.bootstraps import (
    BRIEFCASE_EXIT_SUCCESS_SIGNAL,
    EXIT_SUCCESS_NOTIFY,
    STARTUP_DIAGNOSTICS,
)
from briefcase.bootstraps import PySide6GuiBootstrap


class PySide6AutomationBootstrap(PySide6GuiBootstrap):
    def app_source(self):
        return f"""\
import importlib.metadata
import sys
{STARTUP_DIAGNOSTICS}
checkpoint("interpreter started")
probe_stdout()

from PySide6 import QtWidgets
from PySide6.QtCore import QTimer

checkpoint("PySide6 imported")


class {{{{ cookiecutter.class_name }}}}(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("{{{{ cookiecutter.app_name }}}}")
        self.show()
        checkpoint("main window shown")

        QTimer.singleShot(2000, self.exit_app)

    def exit_app(self):
        checkpoint("exit timer fired")
        # Probe again at the point the exit sentinels are emitted; the state of
        # stdout here is what determines whether Briefcase can see them.
        probe_stdout()
        print("{EXIT_SUCCESS_NOTIFY}")
        print("{BRIEFCASE_EXIT_SUCCESS_SIGNAL}")
        checkpoint("exit sentinels printed")
        QtWidgets.QApplication.quit()


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

    checkpoint("constructing QApplication")
    app = QtWidgets.QApplication(sys.argv)
    checkpoint("QApplication constructed")
    main_window = {{{{ cookiecutter.class_name }}}}()
    checkpoint("entering event loop")
    sys.exit(app.exec())
"""

    def pyproject_table_macOS(self):
        # Include PySide6-Addons on macOS, even though it isn't used, as a way to
        # exercise signing of apps that include nested frameworks and apps. See #1891
        # for details.
        return """\
universal_build = true
# Pyside 6.10 (required for Python 3.14 support) enforces a macOS 13 minimum.
min_os_version = "13.0"
requires = [
    "PySide6-Addons~=6.8",
    "std-nslog~=2.0.0",
]
"""
