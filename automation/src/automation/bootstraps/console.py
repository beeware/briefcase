from automation.bootstraps import BRIEFCASE_EXIT_SUCCESS_SIGNAL, EXIT_SUCCESS_NOTIFY
from briefcase.bootstraps import ConsoleBootstrap


class ConsoleAutomationBootstrap(ConsoleBootstrap):
    def app_source(self):
        return f"""\
import time


def main():
    time.sleep(2)
    print("{EXIT_SUCCESS_NOTIFY}")
    print("{BRIEFCASE_EXIT_SUCCESS_SIGNAL}")
"""
