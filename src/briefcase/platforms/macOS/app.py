import subprocess

from briefcase.commands import (
    BuildCommand,
    CreateCommand,
    PackageCommand,
    PublishCommand,
    RunCommand,
    UpdateCommand
)
from briefcase.config import BaseConfig
from briefcase.exceptions import BriefcaseCommandError
from briefcase.platforms.macOS import macOSMixin, macOSPackageMixin


class macOSAppMixin(macOSMixin):
    output_format = 'app'

    def binary_path(self, app):
        return self.bundle_path(app) / '{app.formal_name}.app'.format(app=app)

    def distribution_path(self, app):
        return self.binary_path(app)

    def entitlements_path(self, app):
        return (
                self.bundle_path(app)
                / 'Entitlements.plist'
        )

class macOSAppCreateCommand(macOSAppMixin, CreateCommand):
    description = "Create and populate a macOS app."


class macOSAppUpdateCommand(macOSAppMixin, UpdateCommand):
    description = "Update an existing macOS app."


class macOSAppBuildCommand(macOSAppMixin, BuildCommand):
    description = "Build a macOS app."


class macOSAppRunCommand(macOSAppMixin, RunCommand):
    description = "Run a macOS app."

    def run_app(self, app: BaseConfig, **kwargs):
        """
        Start the application.

        :param app: The config object for the app
        :param base_path: The path to the project directory.
        """
        print()
        print('[{app.app_name}] Starting app...'.format(
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
                "Unable to start app {app.app_name}.".format(app=app)
            )


class macOSAppPackageCommand(macOSAppMixin, macOSPackageMixin, PackageCommand):
    description = "Package a macOS app for distribution."


class macOSAppPublishCommand(macOSAppMixin, PublishCommand):
    description = "Publish a macOS app."


# Declare the briefcase command bindings
create = macOSAppCreateCommand  # noqa
update = macOSAppUpdateCommand  # noqa
build = macOSAppBuildCommand  # noqa
run = macOSAppRunCommand  # noqa
package = macOSAppPackageCommand  # noqa
publish = macOSAppPublishCommand  # noqa
