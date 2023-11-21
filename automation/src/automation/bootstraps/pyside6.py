from automation.bootstraps import BRIEFCASE_EXIT_SUCCESS_SIGNAL, EXIT_SUCCESS_NOTIFY
from briefcase.bootstraps import PySide6GuiBootstrap


class PySide6AutomationBootstrap(PySide6GuiBootstrap):
    def app_source(self):
        return f"""\
import importlib.metadata
import sys

from PySide6 import QtWidgets
from PySide6.QtCore import QTimer


class {{{{ cookiecutter.class_name }}}}(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("{{{{ cookiecutter.app_name }}}}")
        self.show()

        QTimer.singleShot(2000, self.exit_app)

    def exit_app(self):
        print("{EXIT_SUCCESS_NOTIFY}")
        print("{BRIEFCASE_EXIT_SUCCESS_SIGNAL}")
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

    app = QtWidgets.QApplication(sys.argv)
    main_window = {{{{ cookiecutter.class_name }}}}()
    sys.exit(app.exec())
"""
