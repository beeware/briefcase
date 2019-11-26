import subprocess

from briefcase.commands import (
    BuildCommand,
    CreateCommand,
    PublishCommand,
    RunCommand,
    UpdateCommand
)
from briefcase.config import BaseConfig
from briefcase.exceptions import BriefcaseCommandError
from briefcase.platforms.macOS import macOSMixin


class macOSAppMixin(macOSMixin):
    output_format = 'app'

    def bundle_path(self, app):
        return self.platform_path / '{app.formal_name}.app'.format(app=app)

    def binary_path(self, app):
        return self.bundle_path(app)

    def distribution_path(self, app):
        return self.bundle_path(app)


class macOSAppCreateCommand(macOSAppMixin, CreateCommand):
    description = "Create and populate a macOS .app bundle."


class macOSAppUpdateCommand(macOSAppMixin, UpdateCommand):
    description = "Update an existing macOS .app bundle."


class macOSAppBuildCommand(macOSAppMixin, BuildCommand):
    description = "Build a macOS .app bundle."


class macOSAppRunCommand(macOSAppMixin, RunCommand):
    description = "Run a macOS .app bundle."

    def run_app(self, app: BaseConfig, **kwargs):
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


class macOSAppPublishCommand(macOSAppMixin, PublishCommand):
    description = "Publish a macOS .app bundle."


# Declare the briefcase command bindings
create = macOSAppCreateCommand  # noqa
update = macOSAppUpdateCommand  # noqa
build = macOSAppBuildCommand  # noqa
run = macOSAppRunCommand  # noqa
publish = macOSAppPublishCommand  # noqa
