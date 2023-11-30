from automation.bootstraps import BRIEFCASE_EXIT_SUCCESS_SIGNAL, EXIT_SUCCESS_NOTIFY
from briefcase.bootstraps import PursuedPyBearGuiBootstrap


class PursuedPyBearAutomationBootstrap(PursuedPyBearGuiBootstrap):
    def app_source(self):
        return f"""\
import importlib.metadata
import os
import sys

import ppb


class {{{{ cookiecutter.class_name }}}}(ppb.Scene):
    def __init__(self, **props):
        super().__init__(**props)
        self.updates: int = 0

        self.add(
            ppb.Sprite(
                image=ppb.Image("{{{{ cookiecutter.module_name }}}}/resources/{{{{ cookiecutter.app_name }}}}.png"),
            )
        )

    def on_update(self, event, signal):
        self.updates += 1
        # quit after 2 seconds since on_update is run 60 times/second
        if self.updates > 120:
            print("{EXIT_SUCCESS_NOTIFY}")
            print("{BRIEFCASE_EXIT_SUCCESS_SIGNAL}")
            signal(ppb.events.Quit())


def main():
    # Linux desktop environments use an app's .desktop file to integrate the app
    # in to their application menus. The .desktop file of this app will include
    # the StartupWMClass key, set to app's formal name. This helps associate the
    # app's windows to its menu item.
    #
    # For association to work, any windows of the app must have WMCLASS property
    # set to match the value set in app's desktop file. For PPB, this is set
    # using the SDL_VIDEO_X11_WMCLASS environment variable.

    # Find the name of the module that was used to start the app
    app_module = sys.modules["__main__"].__package__
    # Retrieve the app's metadata
    metadata = importlib.metadata.metadata(app_module)

    os.environ["SDL_VIDEO_X11_WMCLASS"] = metadata["Formal-Name"]

    ppb.run(
        starting_scene={{{{ cookiecutter.class_name }}}},
        title=metadata["Formal-Name"],
    )
"""
