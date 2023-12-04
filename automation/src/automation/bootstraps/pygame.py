from automation.bootstraps import BRIEFCASE_EXIT_SUCCESS_SIGNAL, EXIT_SUCCESS_NOTIFY
from briefcase.bootstraps import PygameGuiBootstrap


class PygameAutomationBootstrap(PygameGuiBootstrap):
    def app_source(self):
        return f"""\
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

    # Set the app's runtime icon
    pygame.display.set_icon(
        pygame.image.load(Path(__file__).parent / "resources/{{{{ cookiecutter.app_name }}}}.png")
    )

    pygame.init()
    pygame.display.set_caption(metadata["Formal-Name"])
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

    pygame.time.set_timer(pygame.QUIT, 2000)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                print("{EXIT_SUCCESS_NOTIFY}")
                print("{BRIEFCASE_EXIT_SUCCESS_SIGNAL}")
                running = False
                break

        screen.fill(WHITE)
        pygame.display.flip()

    pygame.quit()
"""
