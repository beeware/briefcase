from automation.bootstraps import (
    BRIEFCASE_EXIT_SUCCESS_SIGNAL,
    EXIT_SUCCESS_NOTIFY,
    STARTUP_DIAGNOSTICS,
)
from briefcase.bootstraps import TogaGuiBootstrap


class TogaAutomationBootstrap(TogaGuiBootstrap):
    def app_source(self):
        return f'''\
import asyncio
{STARTUP_DIAGNOSTICS}
checkpoint("interpreter started")

import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW

checkpoint("toga imported")


class {{{{ cookiecutter.class_name }}}}(toga.App):
    def startup(self):
        """Construct and show the Toga application.

        Usually, you would add your application to a main content box.
        We then create a main window (with a name matching the app), and
        show the main window.
        """
        checkpoint("app startup")
        main_box = toga.Box()

        self.main_window = toga.MainWindow(title=self.formal_name)
        self.main_window.content = main_box
        self.main_window.show()
        checkpoint("main window shown")

    async def on_running(self):
        """Close the app after a few seconds."""
        checkpoint("event loop running")
        await asyncio.sleep(2)
        print("{EXIT_SUCCESS_NOTIFY}")
        print("{BRIEFCASE_EXIT_SUCCESS_SIGNAL}")
        self.exit()


def main():
    return {{{{ cookiecutter.class_name }}}}()
'''
