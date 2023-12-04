from automation.bootstraps import BRIEFCASE_EXIT_SUCCESS_SIGNAL, EXIT_SUCCESS_NOTIFY
from briefcase.bootstraps import TogaGuiBootstrap


class TogaAutomationBootstrap(TogaGuiBootstrap):
    def app_source(self):
        return f'''\
import asyncio

import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW


class {{{{ cookiecutter.class_name }}}}(toga.App):
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

        self.add_background_task(self.exit_soon)

    async def exit_soon(self, app: toga.App, **kwargs):
        """Background task that closes the app after a few seconds."""
        await asyncio.sleep(2)
        print("{EXIT_SUCCESS_NOTIFY}")
        print("{BRIEFCASE_EXIT_SUCCESS_SIGNAL}")
        self.exit()


def main():
    return {{{{ cookiecutter.class_name }}}}()
'''
