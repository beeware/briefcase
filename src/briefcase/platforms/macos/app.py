import subprocess
from pathlib import Path

from briefcase.config import BaseConfig
from briefcase.commands import (
    BuildCommand,
    CreateCommand,
    PublishCommand,
    RunCommand,
    UpdateCommand
)
from briefcase.exceptions import BriefcaseCommandError
from briefcase.platforms.macos import MacOSMixin


class MacOSAppMixin(MacOSMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, output_format='app', **kwargs)

    def binary_path(self, app):
        return self.platform_path / '{app.formal_name}.app'.format(app=app)

    def bundle_path(self, app):
        return self.platform_path / '{app.formal_name}.app'.format(app=app)


class MacOSAppCreateCommand(MacOSAppMixin, CreateCommand):
    description = "Create and populate a macOS .app bundle."


class MacOSAppUpdateCommand(MacOSAppMixin, UpdateCommand):
    description = "Update an existing macOS .app bundle."


class MacOSAppBuildCommand(MacOSAppMixin, BuildCommand):
    description = "Build a macOS .app bundle."


class MacOSAppRunCommand(MacOSAppMixin, RunCommand):
    description = "Run a macOS .app bundle."

    def run_app(self, app: BaseConfig):
        """
        Start the application.

        :param app: The config object for the app
        :param base_path: The path to the project directory.
        """
        print()
        print('[{app.name}] Starting app...'.format(
            app=app
        ))
        try:
            print()
            self.subprocess.run(
                [
                    'open',
                    self.binary_path(app),
                ],
                check=True,
            )
        except subprocess.CalledProcessError:
            print()
            raise BriefcaseCommandError(
                "Unable to start app {app.name}.".format(app=app)
            )


class MacOSAppPublishCommand(MacOSAppMixin, PublishCommand):
    description = "Publish a macOS .app bundle."


# Declare the briefcase command bindings
create = MacOSAppCreateCommand  # noqa
update = MacOSAppUpdateCommand  # noqa
build = MacOSAppBuildCommand  # noqa
run = MacOSAppRunCommand  # noqa
publish = MacOSAppPublishCommand  # noqa
